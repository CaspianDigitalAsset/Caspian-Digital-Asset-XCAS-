export default {
  async fetch(request, env, ctx) {
    if (request.method !== "POST") {
      return new Response("OK", { status: 200 });
    }

    try {
      const update = await request.json();

      // بررسی پیام تلگرام
      if (update.message && update.message.text) {
        const chatId = update.message.chat.id;
        const text = update.message.text;
        const userName = update.message.from.first_name || "کاربر";

        let responseText = `سلام ${userName}! پیام شما دریافت شد: "${text}"`;

        // مثال نحوه کار با دیتابیس D1 در صورت نیاز
        // const { results } = await env.DB.prepare("SELECT * FROM users WHERE chat_id = ?").bind(chatId).all();

        // ارسال پاسخ به تلگرام
        await sendTelegramMessage(env.TELEGRAM_BOT_TOKEN, chatId, responseText);
      }

      return new Response("OK", { status: 200 });
    } catch (err) {
      return new Response("Error: " + err.message, { status: 500 });
    }
  },
};

async function sendTelegramMessage(token, chatId, text) {
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
    }),
  });
}
