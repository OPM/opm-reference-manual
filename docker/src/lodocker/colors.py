import colorama

def green_color(text: str) -> str:
    return colorama.Fore.GREEN + text + colorama.Fore.RESET

def red_color(text: str) -> str:
    return colorama.Fore.RED + text + colorama.Fore.RESET
