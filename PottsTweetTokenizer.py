#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This code implements a basic, Twitter-aware tokenizer.

A tokenizer is a function that splits a string of text into words. In
Python terms, we map string and unicode objects into lists of unicode
objects.

There is not a single right way to do tokenizing. The best method
depends on the application.  This tokenizer is designed to be flexible
and this easy to adapt to new domains and tasks.  The basic logic is
this:

1. The tuple regex_strings defines a list of regular expression
   strings.

2. The regex_strings strings are put, in order, into a compiled
   regular expression object called word_re.

3. The tokenization is done by word_re.findall(s), where s is the
   user-supplied string, inside the tokenize() method of the class
   Tokenizer.

4. When instantiating Tokenizer objects, there is a single option:
   preserve_case.  By default, it is set to True. If it is set to
   False, then the tokenizer will downcase everything except for
   emoticons.

The __main__ method illustrates by tokenizing a few examples.

I've also included a Tokenizer method tokenize_random_tweet(). If the
twitter library is installed (http://code.google.com/p/python-twitter/)
and Twitter is cooperating, then it should tokenize a random
English-language tweet.
"""

__author__ = "Christopher Potts"
__copyright__ = "Copyright 2011, Christopher Potts"
__credits__ = []
__license__ = "Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License: http://creativecommons.org/licenses/by-nc-sa/3.0/"
__version__ = "1.0"
__maintainer__ = "Christopher Potts"
__email__ = "See the author's website"

######################################################################

import re
import html.entities

######################################################################
# The following strings are components in the regular expression
# that is used for tokenizing. It's important that phone_number
# appears first in the final regex (since it can contain whitespace).
# It also could matter that tags comes after emoticons, due to the
# possibility of having text like
#
#     <:| and some text >:)
#
# Most imporatantly, the final element should always be last, since it
# does a last ditch whitespace-based tokenization of whatever is left.

# This particular element is used in a couple ways, so we define it
# with a name:
emoticon_string = r"""
    (?:
      [<>]?
      [:;=8]                     # eyes
      [\-o\*\']?                 # optional nose
      [\)\]\(\[dDpP/\:\}\{@\|\\] # mouth      
      |
      [\)\]\(\[dDpP/\:\}\{@\|\\] # mouth
      [\-o\*\']?                 # optional nose
      [:;=8]                     # eyes
      [<>]?
    )"""
# Twitter symbols/cashtags:  # Added by awd, 20140410.
# Based upon Twitter's regex described here: <https://blog.twitter.com/2013/symbols-entities-tweets>.
cashtag_string = r"""(?:\$[a-zA-Z]{1,6}([._][a-zA-Z]{1,2})?)"""

# The components of the tokenizer:
regex_strings = (
    # Phone numbers:
    r"""
    (?:
      (?:            # (international)
        \+?[01]
        [\-\s.]*
      )?            
      (?:            # (area code)
        [\(]?
        \d{3}
        [\-\s.\)]*
      )?    
      \d{3}          # exchange
      [\-\s.]*   
      \d{4}          # base
    )"""
    ,
    # Emoticons:
    emoticon_string
    ,
    #URLs, Patch from <https://bitbucket.org/jaganadhg/twittertokenize>
    r"""(?:http[s]?://t.co/[a-zA-Z0-9]+)"""
    ,
    # # HTML tags:
    # r"""(?:<[^>]+>)"""
    # ,
    # Twitter username:
    r"""(?:@[\w_]+)"""
    ,
    # Twitter hashtags:
    r"""(?:\#+[\w_]+[\w\'_\-]*[\w_]+)"""
    ,
    # Twitter cashtags:
    cashtag_string
    ,
    # Remaining word types:
    r"""
    (?:[a-z][a-z'\-_]+[a-z])       # Words with apostrophes or dashes.
    |
    (?:[+\-]?\d+[,/.:-]\d+[+\-]?)  # Numbers, including fractions, decimals.
    |
    (?:[\w_]+)                     # Words without apostrophes or dashes.
    |
    (?:\.(?:\s*\.){1,})            # Ellipsis dots. 
    |
    (?:\S)                         # Everything else that isn't whitespace.
    """
    )

######################################################################
# This is the core tokenizing regex:
    
word_re = re.compile(r"""(%s)""" % "|".join(regex_strings), re.VERBOSE | re.I | re.UNICODE)

# The emoticon and cashtag strings get their own regex so that we can preserve case for them as needed:
emoticon_re = re.compile(emoticon_string, re.VERBOSE | re.I | re.UNICODE)
cashtag_re = re.compile(cashtag_string, re.VERBOSE | re.I | re.UNICODE)

# These are for regularizing HTML entities to Unicode:
html_entity_digit_re = re.compile(r"&#\d+;")
html_entity_alpha_re = re.compile(r"&\w+;")
amp = "&amp;"

######################################################################

class PottsTweetTokenizer:
    def __init__(self, *, preserve_case=False):
        self.preserve_case = preserve_case

    def tokenize(self, tweet: str) -> list:
        """
        Argument: tweet -- any string object.
        Value: a tokenized list of strings; concatenating this list returns the original string if preserve_case=True
        """
        # Fix HTML character entitites:
        tweet = self._html2unicode(tweet)
        # Tokenize:
        matches = word_re.finditer(tweet)
        if self.preserve_case:
            return [match.group() for match in matches]
        # Possibly alter the case, but avoid changing emoticons like :D into :d:
        return [self._normalize_token(match.group()) for match in matches]

    @staticmethod
    def _normalize_token(token: str) -> str:

        if emoticon_re.search(token):
            return token
        if token.startswith('$') and cashtag_re.search(token):
            return token.upper()
        return token.lower()

    @staticmethod
    def _html2unicode(tweet: str) -> str:
        """
        Internal method that seeks to replace all the HTML entities in
        tweet with their corresponding unicode characters.
        """
        # First the digits:
        ents = set(html_entity_digit_re.findall(tweet))
        if len(ents) > 0:
            for ent in ents:
                entnum = ent[2:-1]
                try:
                    entnum = int(entnum)
                    tweet = tweet.replace(ent, chr(entnum))
                except:
                    pass
        # Now the alpha versions:
        ents = set(html_entity_alpha_re.findall(tweet))
        ents = filter((lambda x: x != amp), ents)
        for ent in ents:
            entname = ent[1:-1]
            try:
                tweet = tweet.replace(ent, chr(html.entities.name2codepoint[entname]))
            except:
                pass
            tweet = tweet.replace(amp, " and ")
        return tweet

###############################################################################

if __name__ == '__main__':
    tok = PottsTweetTokenizer()
    samples = (
        u"RT @ #happyfuncoding: this is a typical Twitter tweet :-)",
        u"HTML entities &amp; other Web oddities can be an &aacute;cute <em class='grumpy'>pain</em> >:(",
        u"It's perhaps noteworthy that phone numbers like +1 (800) 123-4567, (800) 123-4567, and 123-4567 are treated as words despite their whitespace.",
        u"$AAPL, http://t.co/asdFGH01, and $GOOG, &lt;https://t.co/asdFGH02&gt;, are battling it out through Google's proxy, Samsung."
        )

    for s in samples:
        print("======================================================================")
        print(s)
        tokenized = tok.tokenize(s)
        print("\n".join(tokenized))
