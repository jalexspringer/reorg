def format_datestring(date_entry):
    """Converts a rethinkdb datestring into Mon, Aug 12, 2016 (for example)"""
    import calendar
    date_string = f'_{calendar.day_abbr[date_entry.weekday()]} {calendar.month_abbr[date_entry.month]} {date_entry.day}, {date_entry.year}_'
    return date_string
