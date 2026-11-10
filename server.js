const fs = require('fs');
const path = require('path');

// --- Мінімальне читання .env (без додаткових залежностей) ---
(function loadEnv() {
    try {
        const envPath = path.join(__dirname, '.env');
        if (!fs.existsSync(envPath)) return;
        fs.readFileSync(envPath, 'utf8').split(/\r?\n/).forEach(line => {
            const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$/);
            if (!m || line.trim().startsWith('#')) return;
            const value = m[2].replace(/^(['"])(.*)\1$/, '$2');
            if (process.env[m[1]] === undefined) process.env[m[1]] = value;
        });
    } catch (e) {
        console.log(`⚠️ Не вдалося прочитати .env: ${e.message}`);
    }
})();

const express = require('express');
const app = express();
const server = require('http').createServer(app);
const io = require('socket.io')(server);
const mineflayer = require('mineflayer');

app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

let activeBots = [];
let botStatus = 'stopped';
let lastConfig = null; // Зберігаємо налаштування для автоперепідключення
let launchTimer = null;

const consoleReport = (msg) => console.log(msg);

// report — функція, яка отримує текст логу (вебсокет, Telegram або консоль)
function createBotInstance(serverHost, serverPort, version, username, report = consoleReport) {
    const botOptions = {
        host: serverHost,
        port: serverPort,
        username: username,
        skipValidation: true
    };

    if (version && version !== 'auto') {
        botOptions.version = version;
    }

    const bot = mineflayer.createBot(botOptions);

    bot.on('spawn', () => {
        botStatus = 'running';
        io.emit('status', 'running');
        report(`✅ Бот [${username}] успішно зайшов на сервер!`);
    });

    bot.on('end', (reason) => {
        report(`❌ Бот [${username}] відключився: ${reason}. Перепідключення через 30 сек...`);

        // Видаляємо старого зі списку і намагаємося перепідключитись через 30 секунд
        activeBots = activeBots.filter(b => b !== bot);

        if (lastConfig && activeBots.length < lastConfig.count) {
            setTimeout(() => {
                if (botStatus === 'running' && lastConfig) {
                    createBotInstance(serverHost, serverPort, version, username, report);
                }
            }, 30000);
        }

        if (activeBots.length === 0 && botStatus === 'running') {
            botStatus = 'stopped';
            io.emit('status', 'stopped');
        }
    });

    bot.on('error', (err) => {
        report(`⚠️ Помилка бота [${username}]: ${err.message}`);
    });

    activeBots.push(bot);
}

// --- Спільна логіка для вебпанелі та Telegram ---

function startBots({ host, count, version }, report = consoleReport) {
    let serverHost = host;
    let serverPort = 25565;

    if (host.includes(':')) {
        const parts = host.split(':');
        serverHost = parts[0];
        serverPort = parseInt(parts[1]) || 25565;
    }

    // Зупиняємо попередніх перед запуском нових
    if (launchTimer) clearInterval(launchTimer);
    activeBots.forEach(b => { try { b.quit(); } catch (e) {} });
    activeBots = [];

    lastConfig = { serverHost, serverPort, version, count };
    botStatus = 'running';
    io.emit('status', 'running');

    report(`🔄 Запуск ${count} ботів на сервері ${serverHost}:${serverPort}...`);

    // Запускаємо ботів з невеликою затримкою між ними (по 1.5 секунди), щоб не спамити сервер
    let launched = 0;
    launchTimer = setInterval(() => {
        if (launched >= count || botStatus === 'stopped') {
            clearInterval(launchTimer);
            launchTimer = null;
            return;
        }
        launched++;
        const username = `AtenBot_${Math.floor(Math.random() * 900) + 100}`;
        createBotInstance(serverHost, serverPort, version, username, report);
    }, 1500);
}

function stopBots(report = consoleReport) {
    botStatus = 'stopped';
    lastConfig = null;
    if (launchTimer) {
        clearInterval(launchTimer);
        launchTimer = null;
    }
    report('🛑 Зупинка всіх ботів...');
    activeBots.forEach(b => {
        try { b.quit(); } catch (e) {}
    });
    activeBots = [];
    io.emit('status', 'stopped');
}

function sendBotCommand(command, report = consoleReport) {
    if (activeBots.length === 0) {
        report('⚠️ Немає активних ботів для виконання команди!');
        return;
    }

    report(`💬 Відправка команди: ${command}`);
    // Перший бот у списку відправляє команду в чат
    try {
        activeBots[0].chat(command);
    } catch (e) {
        report(`❌ Помилка відправки команди: ${e.message}`);
    }
}

// --- Вебпанель (socket.io) ---

io.on('connection', (socket) => {
    socket.emit('status', botStatus);
    const report = (msg) => socket.emit('log', msg);

    socket.on('start-bot', (data) => {
        const { host, version } = data;
        const count = Math.max(1, parseInt(data.count) || 1);
        startBots({ host, count, version }, report);
    });

    socket.on('stop-bot', () => {
        stopBots(report);
    });

    socket.on('send-command', (data) => {
        sendBotCommand(data.command, report);
    });
});

// --- Telegram-бот (long polling, без залежностей; потрібен Node 18+) ---

const TELEGRAM_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
// Необов'язково: список ID чатів через кому, яким дозволено керувати ботом
const TELEGRAM_ALLOWED = (process.env.TELEGRAM_ALLOWED_IDS || '')
    .split(',').map(s => s.trim()).filter(Boolean);

const TELEGRAM_HELP = [
    '🤖 Керування Minecraft-ботами:',
    '/run <IP[:порт]> [кількість] [версія] — запустити (версія за замовчуванням auto)',
    '/stop — зупинити всіх ботів',
    '/say <текст або /команда> — написати в чат від імені першого бота',
    '/status — поточний стан',
    '/help — ця підказка'
].join('\n');

async function telegramApi(method, params = {}) {
    const res = await fetch(`https://api.telegram.org/bot${TELEGRAM_TOKEN}/${method}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    });
    return res.json();
}

async function telegramSend(chatId, text) {
    try {
        // Telegram дозволяє максимум 4096 символів у повідомленні
        await telegramApi('sendMessage', { chat_id: chatId, text: String(text).slice(0, 4096) });
    } catch (e) {
        console.log(`⚠️ Не вдалося надіслати повідомлення в Telegram: ${e.message}`);
    }
}

async function handleTelegramMessage(message) {
    const chatId = message.chat.id;
    const text = (message.text || '').trim();
    if (!text.startsWith('/')) return;

    if (TELEGRAM_ALLOWED.length && !TELEGRAM_ALLOWED.includes(String(chatId)) &&
        !TELEGRAM_ALLOWED.includes(String(message.from && message.from.id))) {
        await telegramSend(chatId, '⛔ Немає доступу.');
        return;
    }

    const report = (msg) => telegramSend(chatId, msg);
    const [rawCmd, ...args] = text.split(/\s+/);
    const cmd = rawCmd.split('@')[0].toLowerCase();

    switch (cmd) {
        case '/start':
        case '/help':
            await telegramSend(chatId, TELEGRAM_HELP);
            break;

        case '/run': {
            if (!args[0]) {
                await telegramSend(chatId, 'Використання: /run <IP[:порт]> [кількість] [версія]');
                break;
            }
            const count = Math.max(1, parseInt(args[1]) || 1);
            const version = args[2] || 'auto';
            startBots({ host: args[0], count, version }, report);
            break;
        }

        case '/stop':
            stopBots(report);
            break;

        case '/say': {
            const command = args.join(' ');
            if (!command) {
                await telegramSend(chatId, 'Використання: /say <текст або /команда>');
                break;
            }
            sendBotCommand(command, report);
            break;
        }

        case '/status': {
            const cfg = lastConfig
                ? `\nСервер: ${lastConfig.serverHost}:${lastConfig.serverPort}, версія: ${lastConfig.version || 'auto'}, потрібно ботів: ${lastConfig.count}`
                : '';
            await telegramSend(chatId, `Статус: ${botStatus === 'running' ? 'працює 🟢' : 'зупинено 🔴'}\nАктивних ботів: ${activeBots.length}${cfg}`);
            break;
        }

        default:
            await telegramSend(chatId, 'Невідома команда. /help — список команд.');
    }
}

async function startTelegramBot() {
    if (!TELEGRAM_TOKEN) {
        console.log('ℹ️ TELEGRAM_BOT_TOKEN не задано — Telegram-бот вимкнено.');
        return;
    }
    if (!TELEGRAM_ALLOWED.length) {
        console.log('⚠️ TELEGRAM_ALLOWED_IDS не задано — командувати ботом може будь-хто, хто знайде його в Telegram.');
    }

    const sleep = (ms) => new Promise(r => setTimeout(r, ms));
    let offset = 0;
    console.log('🤖 Telegram-бот запущено (long polling).');

    while (true) {
        try {
            const data = await telegramApi('getUpdates', {
                offset,
                timeout: 30,
                allowed_updates: ['message']
            });

            if (!data.ok) {
                console.log(`⚠️ Telegram API: ${data.description || 'невідома помилка'}`);
                await sleep(5000);
                continue;
            }

            for (const update of data.result) {
                offset = update.update_id + 1;
                if (update.message) {
                    handleTelegramMessage(update.message).catch(e =>
                        console.log(`⚠️ Помилка обробки Telegram-повідомлення: ${e.message}`));
                }
            }
        } catch (e) {
            console.log(`⚠️ Помилка Telegram polling: ${e.message}`);
            await sleep(5000);
        }
    }
}

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
    console.log(`Сервер запущено на порту ${PORT}`);
    startTelegramBot();
});
