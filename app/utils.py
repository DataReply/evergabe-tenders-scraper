from datetime import datetime

from dateutil.relativedelta import relativedelta


def get_date_one_month_from_now():
    return (datetime.now() + relativedelta(months=1)).strftime("%d.%m.%Y")
