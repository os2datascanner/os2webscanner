#This needs to be handled in a better way!
from exchangelib import EWSDateTime, EWSTimeZone
tz = EWSTimeZone.localzone()
start_date = tz.localize(EWSDateTime(2018, 1, 31, 0, 0))

export_path = '/mnt/new_var/mailscan/users/'
mail_ending = '@vordingborg.dk'
user_path = './user.txt'

