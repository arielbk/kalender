import calendar, datetime

now = datetime.datetime.now()

cal_data = calendar.monthcalendar(now.year, now.month)
print(cal_data)
