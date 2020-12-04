from pathlib import Path

import attr
import lingpy
import pylexibank
from pylexibank import Dataset as BaseDataset
from clldutils.misc import slug
from clldutils.text import strip_brackets
from lingpy.sequence.sound_classes import syllabify

from cldfbench import CLDFSpec
from csvw import Datatype
from pyclts import CLTS



def is_chinese(name):
    """
    Taken from http://stackoverflow.com/questions/16441633/python-2-7-test-if-characters-in-a-string-are-all-chinese-characters
    """
    if not name:
        return False
    for ch in name:
        ordch = ord(ch)
        if not (0x3400 <= ordch <= 0x9fff) and not (0x20000 <= ordch <= 0x2ceaf) \
                and not (0xf900 <= ordch <= ordch) and not (0x2f800 <= ordch <= 0x2fa1f): 
                return False
    return True


def clean_entry(string):
    """simple replacements to enhance segmentation"""
    st = [
            (':' ,'ː'),
            ('.' ,''),
            ('=' ,''),
            (' ', '_'),
            ('_LF', ''),
            ]
    mapper = dict(zip('0123456789', '⁰¹²³⁴⁵⁶⁸⁹'))
    mapper.update(dict(st))
    string = string.strip(' ')
    string = string.strip('-')
    string = ''.join([x for x in string if not is_chinese(x)])
    string = string.strip('_')
    string = string.split(',')[0]
    string = string.strip('_')
    return strip_brackets(
            ''.join([mapper.get(s, s) for s in string.strip()])
            )

@attr.s
class CustomConcept(pylexibank.Concept):
    Number = attr.ib(default=None)


@attr.s
class CustomLanguage(pylexibank.Language):
    Number = attr.ib(default=None)
    Database = attr.ib(default=None)
    Abbreviation = attr.ib(default=None)
    Note = attr.ib(default=None)



class Dataset(BaseDataset):
    dir = Path(__file__).parent
    id = "peirosst"
    concept_class = CustomConcept
    language_class = CustomLanguage
    form_spec = pylexibank.FormSpec(
            replacements=[
                ("❷", ""), ("&quot;", ""),
                (':' ,'ː'),
                ('.' ,''),
                ('=' ,''),
                (' ', '_'),
                ('_LF', '')],
            )


    def cmd_makecldf(self, args):
        data = self.raw_dir.read_csv('st-data.tsv', delimiter='\t',
                dicts=True)

        args.writer.add_sources()


        # note: no way to easily replace this with the direct call to `add_concepts`
        # as we add the Chinese gloss via concept.attributes
        concepts = {}
        for concept in self.conceptlists[0].concepts.values():
            idx = concept.id.split("-")[-1] + "_" + slug(concept.english)
            args.writer.add_concept(
                ID=idx,
                Name=concept.english,
                Number=concept.number,
                Concepticon_ID=concept.concepticon_id,
                Concepticon_Gloss=concept.concepticon_gloss,
            )
            concepts[concept.number] = idx

        languages = args.writer.add_languages(lookup_factory="Abbreviation")
        
        visited = set()
        for row in pylexibank.progressbar(data[1:], desc='cldfify',
                total=len(data)):
            for language in map(lambda x: x.upper(), languages):
                if language in row:
                    if row[language].strip():
                        entry = clean_entry(row[language])
                        if entry.strip():
                            lexeme = args.writer.add_form(
                                    Language_ID=languages[language.lower()],
                                    Parameter_ID=concepts[row['NUMBER']],
                                    Value=row[language],
                                    Form=entry,
                                    Source='Peiros2004'
                                    )
                            args.writer.add_cognate(
                                    lexeme=lexeme,
                                    Cognateset_ID="{0}-{1}".format(
                                        row['NUMBER'],
                                        row[language+'NUM']),
                                    Source='Peiros2004'
                          )
                else:
                    if language not in visited:
                        visited.add(language)
                        print(language)
                        



 
