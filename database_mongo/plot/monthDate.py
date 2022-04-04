
def get_month(got_month):
    got_month = str(got_month).lower()
    month, addition = {
        'jan': [1, 'January'],
        'january': [1, 'January'],
        'feb': [2, 'February'],
        'february': [2, 'February'],
        'mar': [3, 'March'],
        'march': [3, 'March'],
        'apr': [4, 'April'],
        'april': [4, 'April'],
        'may': [5, 'May'],
        'jun': [6, 'June'],
        'june': [6, 'June'],
        'jul': [7, 'July'],
        'july': [7, 'July'],
        'aug': [8, 'August'],
        'august': [8, 'August'],
        'sept': [9, 'September'],
        'september': [9, 'September'],
        'oct': [10, 'October'],
        'october': [10, 'October'],
        'nov': [11, 'November'],
        'november': [11, 'November'],
        'dec': [12, 'December'],
        'december': [12, 'December'],
    }[got_month]

    return addition, month
