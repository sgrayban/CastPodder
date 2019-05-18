#! python
# -*- coding: utf-8 -*-
#
# $Id: __init__.py 68 2006-04-26 20:14:35Z sgrayban $

# translations go in this directory

language_names = {   
    'ab' : u" аҧсуа бызшәа",
    'af' : u"Afrikaans",
    'am' : u" አማርኛ",
    'ar' : u"العربية",
    'az' : u"Azərbaycan",
    'be' : u"Беларуская",
    'bg' : u"Български",
    'bm' : u"Bamanankan",
    'ca' : u"Català",
    'cs' : u"čeština",
    'cy' : u"Cymraeg",
    'da' : u"Dansk",
    'de' : u"Deutsch",
    'ee' : u"Ɛʋɛ",
    'el' : u"Ελληνικά",
    'en' : u"English",
    'es' : u"Español",
    'et' : u"Eesti",
    'eu' : u"Euskara",
    'fa' : u"فارسی",
    'ff' : u"Fulfulde, Pulaar, Pular",
    'fi' : u"Suomi",
    'fr' : u"Français",
    'fr-CA' : u"Français canadien",
    'ga' : u"Gaeilge",
    'gl' : u"Galego",
    'ha' : u"Hausa",
    'he' : u"עברית",
    'hi' : u"हिंदी",
    'hr' : u"Hrvatski",
    'hu' : u"Magyar",
    'hy' : u"Հայերեն",
    'id' : u"Bahasa indonesia",
    'is' : u"Íslenska",
    'it' : u"Italiano",
    'ja' : u"日本語",
    'ka' : u"ქართული ",
    'kk' : u"Қазақ",
    'kn' : u"ಕನ್ನಡ",
    'ko' : u"한국어",
    'ky' : u"Кыргыз",
    'lt' : u"Lietuviškai",
    'luo' : u"Dholuo",
    'lv' : u"Latviešu",
    'mk' : u"Македонски",
    'ms' : u"Bahasa melayu",
    'mt' : u"Malti",
    'nl' : u"Nederlands",
    'no' : u"Norsk",
    'pl' : u"Polski",
    'ps' : u" پښتو",
    'pt' : u"Português",
    'pt-BR' : u"Português brasileiro",
    'rn' : u"Kirundi",
    'ro' : u"Română",
    'ru' : u"Pyccĸий",
    'rw' : u"Kinyarwanda",
    'sk' : u"Slovenčina",
    'sl' : u"Slovenščina",
    'so' : u"Somali",
    'sq' : u"Shqip",
    'sr' : u"Srpski Српски",
    'sv' : u"Svenska",
    'sw' : u"Kiswahili",
    'te' : u"తెలుగు",
    'th' : u"ภาษาไทย",
    'tr' : u"Tϋrkçe",
    'uk' : u"Українська",
    'ur' : u"اردو",
    'uz' : u"o'zbek",
    'vi' : u"Tiếng Việt",
    'wo' : u"Wolof",
    'xs' : u"IsiXhosa",
    'yo' : u"Yorùbá",
    'zh' : u"中文",
    'zh-Hans' : u"简体中文",
    'zh-Hant' : u"繁體中文",
    'zu' : u"IsiZulu",
}

def get_language_name(code):
    if language_names.has_key(code):
        return language_names[code]
    else:
        return code
    
