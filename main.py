import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from datetime import datetime, timedelta
import pytz  # Importa la biblioteca pytz

# Conexión con nuestro bot
TOKEN = '7722475502:AAHv36QJX-dJhl9uDw0QFRusEZRVyv9m0So'
bot = telebot.TeleBot(TOKEN)

# Diccionario para almacenar eventos {user_id: fecha_evento}
eventos = {}

# Inicializar el programador de tareas
scheduler = BackgroundScheduler()
scheduler.start()

# Establecer la zona horaria de Buenos Aires
tz = pytz.timezone('America/Argentina/Buenos_Aires')

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Hola! Soy el asistente de alarma de sesión!')

# Comando /help
@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, 'Puedo ayudarte a programar recordatorios. Usa /agregar para agendar un evento.')

# Comando /agregar
@bot.message_handler(commands=['agregar'])
def send_options(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_si = types.InlineKeyboardButton('Sí', callback_data='Agregar_si')
    btn_no = types.InlineKeyboardButton('No', callback_data='Agregar_no')
    markup.add(btn_si, btn_no)
    bot.reply_to(message, "¿Estás planeando una sesión?", reply_markup=markup)

# Manejo de respuestas a los botones
@bot.callback_query_handler(func=lambda call: True)
def call_query(call):
    if call.data == 'Agregar_si':
        bot.send_message(call.message.chat.id, '¡Genial! Envíame la fecha y hora en el formato: DD-MM-YYYY HH:MM')
        bot.register_next_step_handler(call.message, recibir_fecha)
    elif call.data == 'Agregar_no':
        bot.send_message(call.message.chat.id, 'No hay problema. Avísame si necesitas algo.')

# Función para recibir la fecha del usuario
def recibir_fecha(message):
    try:
        # Convertir la fecha a la zona horaria de Buenos Aires
        fecha_evento = datetime.strptime(message.text, "%d-%m-%Y %H:%M")
        fecha_evento = tz.localize(fecha_evento)  # Aplicar la zona horaria
        eventos[message.chat.id] = fecha_evento
        bot.reply_to(message, f'Evento guardado para {fecha_evento.strftime("%d-%m-%Y %H:%M")}. Te avisaré cuando llegue el momento.')

        # Programar alertas previas
        scheduler.add_job(enviar_alerta, 'date', run_date=fecha_evento - timedelta(hours=2), args=[message.chat.id, "⏰ ¡Recuerda, tu sesión inicia en 2 horas!"])
        scheduler.add_job(enviar_alerta, 'date', run_date=fecha_evento - timedelta(hours=1), args=[message.chat.id, "⏰ ¡Recuerda, tu sesión inicia en 1 hora!"])
        scheduler.add_job(enviar_alerta, 'date', run_date=fecha_evento - timedelta(minutes=30), args=[message.chat.id, "⏰ ¡Recuerda, tu sesión inicia en 30 minutos!"])

        # Programar la alerta final
        scheduler.add_job(enviar_alerta, 'date', run_date=fecha_evento, args=[message.chat.id, "⏰ ¡Es hora de tu sesión programada!"])

    except ValueError:
        bot.reply_to(message, "Formato incorrecto. Usa: DD-MM-YYYY HH:MM")
        bot.register_next_step_handler(message, recibir_fecha)

# Función para enviar la alerta cuando llegue el momento
def enviar_alerta(chat_id, mensaje):
    bot.send_message(chat_id, mensaje)

# Iniciar el bot
if __name__ == "__main__":
    bot.polling(none_stop=True)