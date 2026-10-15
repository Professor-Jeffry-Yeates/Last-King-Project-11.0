__version__ = '8.0'
class VocabularyQuizGeneral():
    """General definition in the main program. These are general to many mapsc so they will be added to with each new map.
    Note that vocabulary errors result in a blank string. That can be adventageous as some objects have pre and post adjectives,
    and some do not.  The blank will not be noticed."""
    def __init__( self, specificVocabulary=None):
        self.additionalVocabulary = specificVocabulary

    def setup(self, data):
        vocab = data.vocab

        #  Add any specific initializations for normal vocabulary. Normally they are file based. 
        #  Syntax is dictionary/file name (.txt) and list, tuple, or list of CSV individual words.
        vocab.addNormalVocabulary("emotional_response",["suprised","terrified","interested","astonished","amazed","startled","shocked","stunned","flabbergasted","dumbfounded","bewildered","astounded","taken aback","gobsmacked","speechless","baffled","aghast","alarmed","overjoyed","delighted","disconcerted","perplexed","thunderstruck"])
        vocab.addNormalVocabulary("emotional_outburst","Wow,Zowie,Shazam,Whoppie,Huzzah,Yikes,Gadzooks,Bravo,Eureka,Aha,Whew,Yowza,Voila,Hurrah,Bingo,Yippee,Zoinks,Booyah,Ta-da,Whoops,Leaping lizards")

        # Special vocabularies
        #  Syntax is dictionary/file name (.txt), dictionary of special values, and list, tuple, or list of CSV individual words.
        vocab.addSpecialVocabulary( "thought_what_next", {"RANDOM":"WEIGHTED"}, ["Onward to glory and death!","Must think but it hurts my head to think!","Is it lunch time yet?"])
        vocab.addSpecialVocabulary( "random_object", {"RANDOM":"USE_ONCE"}, vocab.extractListFromFile("random_object"))
        # Definitions
        #  Syntax is dictionary name, formatting-based string expecting the main type to be first in the format arguments (such as 'scroll').
                 
        # Content, {0} is the treasure type
        #  Syntax is dictionary name, formatting-based string of each random type to put formatted into a definition string.
        #  The main type (such as scroll) is used to replace the {0} for type-specific file-based values. Suggest same names.
        vocab.addDefinition( "enterRoom",'{1} a {2} {0}{3}. You are {4} and yell "{5}"! Oh well. {6}')
        vocab.addContent( "enterRoom","verb_room_entered,pre_adj_{0},post_adj_{0},emotional_response,emotional_outburst,thought_what_next")
        
        vocab.addDefinition( "standard_sword", "You {1} a {0} {2}, and it's {3}" )
        vocab.addContent( "standard_sword", "adv_object_finding,adv_object_location,adj_weapon" )
        
        vocab.addDefinition( "standard_damaged_sword", "You {1} a {0} {2}, and it's {3}" )
        vocab.addContent( "standard_damaged_sword", "adv_object_finding,adv_object_location,adj_weapon" )
                
        vocab.addDefinition( "standard_broken_sword", "You {1} a {0} {2}, and it's {3}" )
        vocab.addContent( "standard_broken_sword", "adv_object_finding,adv_object_location,adj_weapon" )
        
        vocab.addDefinition( "standard_spider",'The torchlight reveals a {1} {0} in the room. She {2}, {3}, and has decorated clawed-nails {4}. The most beautiful you have ever seen. All eight feet are {4}! You are both {5} and {6}, and yell "{7}"!')
        vocab.addContent( "standard_spider", "adj_big,adj_{0}_looks,adj_{0}_persona,adj_{0}_nails,emotional_response,emotional_response,emotional_outburst")
        
        # Add in or replace with additional vocabulary object
        if self.additionalVocabulary is not None:
            self.additionalVocabulary.setup(vocab)