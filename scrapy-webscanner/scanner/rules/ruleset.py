# The contents of this file are subject to the Mozilla Public License
# Version 2.0 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
#    http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# OS2Webscanner was developed by Magenta in collaboration with OS2 the
# Danish community of open source municipalities (http://www.os2web.dk/).
#
# The code is currently governed by OS2 the Danish community of open
# source municipalities ( http://www.os2web.dk/ )
"""A set of regular expression-based rules."""
import re
import regex
import logging
from ..items import MatchItem

from os2webscanner.models.regexrule_model import RegexRule


# See https://www.jetbrains.com/help/idea/remote-debugging.html#1

class RuleSet():
    """
    This class encapsulates a collection/set of rules that need to be run
    against an object (i.e. file or web(app) page/site
    """

    def __init__(self, name, rules, sensitivity):
        # Convert QuerySet to list
        self.rules_list = list(rules.all())
        logging.debug('Rules is now list: ' + str(type(self.rules_list) is list))
        print('Rules 1 is RegexRule: ' + str(type(self.rules_list[0]) is RegexRule))
        for _psuedoRule in self.rules_list:
            logging.debug(('----------------')
            logging.debug((_psuedoRule)
        logging.debug(('-----------\n')
        # self.rule_set = set(rules)
        self.sensitivity = sensitivity
        self.name = name
        self.regex_str = self.compund_rules()
        self.regex = regex.compile(self.regex_str, regex.DOTALL)

    def compund_rules(self):
        """
        What this method does is it compounds al the rules in the rule set into one regex rule that is OR'ed
        e.g. A ruleSet of {rule1, rule2, rule3} becomes (rule1 | rule2 | rule3)
        :return: RegexRule representing the compound rule
        """

        rule_set = set(self.rules_list)
        if len(rule_set) == 1:
            return rule_set.pop().match_string
        if len(rule_set) > 1:
            compound_rule = '('
            for _ in self.rules_list:
                compound_rule += rule_set.pop().match_string
                if len(rule_set) <= 0:
                    compound_rule += ')'
                else:
                    compound_rule += ' | '
            print('The compounded rule for the rule set is: ' + compound_rule)
            return compound_rule

    def execute(self, text):
        """
        Executes the compounded rule on the text.
        :param text: the text to search
        :return: a set of matches for the rule
        """
        matches = set()
        re_matches = self.regex.finditer(text)
        for match in re_matches:
            matched_data = match.group(0)
            if len(matched_data) > 1024:
                # TODO: Get rid of magic number
                matched_data = match.group(1)
            matches.add(MatchItem(matched_data=matched_data,
                                  sensitivity=self.sensitivity))
        return matches

    def isAllMatch(self, matches):
        """
        Checks if each rule is matched with the provided list of matches
        :param matches: List of matches
        :return: {True | false}
        """
        if not isinstance(matches, set):
            return False

        for rule in self.rules_list:
            rule_set = set(self.rules_list)
            for match in matches:
                print('The matched data vs matched_string' + rule.match_string + ' :: ' + match.matched_data)
                if re.match(rule.match_string, match.matched_data):
                    rule_set.pop()
                    continue

        if not rule_set:
            return True
        else:
            return False

    def __rules_list_to_set(self):
        rules = set()
        if not self.rules_list:
            return None
        for rule in self.rules_list:
            print('Rule => ' + str(rule) + '\n')
            rules.add(RegexRule(
                name=rule.get('name'),
                match_string=rule.get('match_string'),
                sensitivity=rule.get('sensitivity'),
                organization_id=rule.get('organization_id'),
                id=rule.get('id')
            ))
        return rules

    def __str__(self):
        """
        Returns a string object repreesentation of this object
        :return:
        """
        return '{\n\tname: ' + self.name + \
               ',\n\tregex: ' + self.regex_str + \
               ',\n\tsensitivity: ' + str(self.sensitivity) + '\n}'
