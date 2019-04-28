from datetime import datetime

def _df(seconds, denominator=1, text='', past=True):
    core = str(int((seconds + denominator // 2) // denominator)) + text
    if past:
        return core + ' ago'
    else:
        return 'in ' + core


def date(time, asdays=False, short=False):
    '''Returns a pretty formatted date.
    Inputs:
        time is a datetime object or an int timestamp
        asdays is True if you only want to measure days, not seconds
        short is True if you want "1d ago", "2d ago", etc. False if you want
    '''

    now = datetime.now()
    if isinstance(time, int):
        time = datetime.fromtimestamp(time)

    if time > now:
        past, diff = False, time - now
    else:
        past, diff = True, now - time
    seconds = diff.seconds
    days = diff.days

    if short:
        if days == 0 and not asdays:
            if seconds <= 4:
                return 'now'
            elif seconds < 60:
                return _df(seconds, 1, 's', past)
            elif seconds < 3600:
                return _df(seconds, 60, 'm', past)
            else:
                return _df(seconds, 3600, 'h', past)
        else:
            if days == 0:
                return 'today'
            elif days == 1:
                return 'yest' if past else 'tom'
            elif days < 7:
                return _df(days, 1, 'd', past)
            elif days < 31:
                return _df(days, 7, 'w', past)
            elif days < 365:
                return _df(days, 30, 'mo', past)
            else:
                return _df(days, 365, 'y', past)
    else:
        if days == 0 and not asdays:
            if seconds <= 4:
                return 'now'
            elif seconds < 60:
                return _df(seconds, 1, ' seconds', past)
            elif seconds < 120:
                return 'a minute ago' if past else 'in a minute'
            elif seconds < 3600:
                return _df(seconds, 60, ' minutes', past)
            elif seconds < 7200:
                return 'an hour ago' if past else 'in an hour'
            else:
                return _df(seconds, 3600, ' hours', past)
        else:
            if days == 0:
                return 'today'
            elif days == 1:
                return 'yesterday' if past else 'tomorrow'
            elif days == 2:
                return 'day before' if past else 'day after'
            elif days < 7:
                return _df(days, 1, ' days', past)
            elif days < 14:
                return 'last week' if past else 'next week'
            elif days < 31:
                return _df(days, 7, ' weeks', past)
            elif days < 61:
                return 'last month' if past else 'next month'
            elif days < 365:
                return _df(days, 30, ' months', past)
            elif days < 730:
                return 'last year' if past else 'next year'
            else:
                return _df(days, 365, ' years', past)