from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from builtins import str
from future import standard_library
standard_library.install_aliases()
import argparse
import functools
import logging
import traceback
import osaka.main
import osaka.utils


def argparse_exception_wrapper(function, arg):
    '''
    A function wrapper that converts exceptions into an arg-parse type exception
    @param function - function to call (typically bound using functools.partial)
    @param arg - argument to check
    '''
    try:
        function(arg)
    except Exception as e:
        raise argparse.ArgumentTypeError(str(e))
    return arg


def get_main_parser():
    ''' Gets the top-level parser '''
    parser = argparse.ArgumentParser(
        prog="osaka", description="Mosura-CLI for Osaka")
    parser.add_argument("-v", "--verbose", help="Enables verbose output",
                        action="store_true", default=False)
    parser.add_argument("-d", "--debug", help="Enables debug output",
                        action="store_true", default=False)
    subparsers = parser.add_subparsers(help='sub-command help', dest="cmd")
    add_get_parser(subparsers)
    add_put_parser(subparsers)
    add_rm_parser(subparsers)
    add_size_parser(subparsers)
    add_list_parser(subparsers)
    parser_ex = subparsers.add_parser("exists", description="Check the existence of the specified source Osaka-URL",
                                      help="'exists' sub-command help")
    parser_ex.add_argument("source", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                           help="The source Osaka-URL to remove")
    parser_ex = subparsers.add_parser(
        "gojira", description="RRRRRRAAAAAAAWWW...", help="RRRRRRAAAAAAAWWW...")
    return parser


def add_get_parser(subparsers):
    ''' Osaka GET command line '''
    parser_get = subparsers.add_parser("get", description="Retrieves the specified Osaka-URL to specified destination",
                                       help="'get' sub-command help")
    parser_get.add_argument(
        "-f", "--force", help="Forces a retrieval of the source Osaka-URL", action="store_true", default=False)
    parser_get.add_argument("-x", "--no-coop", help="Refuses to cooperate with other osaka processes",
                            action="store_true", default=False, dest="ncoop")
    parser_get.add_argument("-n", "--no-clobber", help="Refuses to clobber existing destinations",
                            action="store_true", default=False, dest="noclobber")
    parser_get.add_argument("source", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                            help="The source Osaka-URL to get")
    parser_get.add_argument("destination", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                            nargs="?",
                            default="./",
                            help="The destination Osaka-URL to place result. Defaults to CWD")


def add_put_parser(subparsers):
    ''' Osaka PUT command line '''
    parser_put = subparsers.add_parser("put", description="Puts the specified source Osaka-URL to specified destination Osaka-URL",
                                       help="'put' sub-command help")
    parser_put.add_argument("-x", "--no-coop", help="Refuses to cooperate with other osaka processes",
                            action="store_true", default=False, dest="ncoop")
    parser_put.add_argument("-n", "--no-clobber", help="Refuses to clobber existing destinations",
                            action="store_true", default=False, dest="noclobber")
    parser_put.add_argument("source", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                            help="The source Osaka-URL to put")
    parser_put.add_argument("destination", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                            help="The destination Osaka-URL to place result")


def add_rm_parser(subparsers):
    ''' Osaka RM command line '''
    parser_rm = subparsers.add_parser("rm", description="Remove the specified source Osaka-URL",
                                      help="'rm' sub-command help")
    parser_rm.add_argument("source", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                           help="The source Osaka-URL to remove")
    parser_rm.add_argument("-f", "--force", dest="unlock",
                           help="Force unlock before removal", action='store_true', default=False)


def add_size_parser(subparsers):
    ''' Osaka size command line '''
    parser_size = subparsers.add_parser("size", description="Returns the size of the specified source Osaka-URL",
                                        help="'size' sub-command help")
    parser_size.add_argument("source", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                             help="The source Osaka-URL to size")
    parser_size.add_argument("-f", "--force", dest="force",
                             help="Force sizing for locked urls", action='store_true', default=False)


def add_list_parser(subparsers):
    ''' Osaka size command line '''
    parser_ls = subparsers.add_parser("list", description="Returns the recursive listing of the specified source Osaka-URL",
                                      help="'list' sub-command help")
    parser_ls.add_argument("source", type=functools.partial(argparse_exception_wrapper, osaka.base.StorageBase.getStorageBackend),
                           help="The source Osaka-URL to list children")
    parser_ls.add_argument("-f", "--force", dest="force",
                           help="Force sizing for locked urls", action='store_true', default=False)


def main(args=None):
    '''
    Entry-point for the main osaka-cli
    '''
    parsed = get_main_parser().parse_args(args)
    # Setup logging levels
    if parsed.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    # Rename 'rm' command
    parsed.cmd = "rmall" if parsed.cmd == "rm" else parsed.cmd
    params = []
    for item in ["source", "destination"]:
        if item in parsed:
            params.append(getattr(parsed, item))
    kwargs = {}
    for item in ["unlock", "force", "ncoop", "noclobber"]:
        if item in parsed:
            kwargs[item] = getattr(parsed, item)
    if parsed.cmd == "gojira":
        gojira()
        return 0
    try:
        fn = getattr(osaka.main, parsed.cmd)
        ret = fn(*params, **kwargs)
        if parsed.cmd == "exists":
            text = "Found" if ret else "Not Found"
            print("{0}: {1}".format(text, parsed.source))
        elif parsed.cmd == "size":
            sz, lb = osaka.utils.human_size(ret)
            print("Size {0} {1}: {2}".format(sz, lb, parsed.source))
        elif parsed.cmd == "list":
            print("Listing for: {0}".format(parsed.source))
            for listing in ret:
                print("  {0}".format(listing))
    except Exception as e:
        print("[ERROR] An exception of type {0} occured with message '{1}'".format(
            type(e).__name__, e))
        if parsed.debug:
            traceback.print_exc()
        return -1
    return 0


def gojira():
    '''
    A Gojira egg
    '''
    moth = '''
                      '####++###+++++++++++++++++#############+++++++++++++++++++#################################+'                                            
                        '############+++++++++##############++++++++++++++++++++####################################+'                                          
                          +#####++######################+++++++++++###################################################+                                         
                            ++################++############+++++++++++++##############################################+                                        
                              '++++++++++++++####################++++++++++++++++######################################+                            '           
                                '++++++++++''+++++++++++++++#########+++++++++++++++++###############################+'      ``````'++++++++++```+++++'         
                                   '########++++++++++++++++++++++##+++++++++++++++++++++++++++++++++##############+''    ```++++##++#########+++++++++'        
   ```''                             '+#++##+++#########++####+++++++++++++++++++++++++++++++++++++++++#########+''   ''+++++++###+################++++++'      
 '++'++''                               '+#++++++#+++######++++##+######+++++++++++++++++++++++++++++++++++####'  ''+++++++#########################+++++++''   
 +++``````''                               +++++++++++++++++++++++++++++++++++++++++++######+#####++++++++++++```+++#+++#######+#####################+++++++'   
  '+```;```;;'';                              '++++++''++++++++++++++++++######++++#+++++#++###+####++++++++++++########++##++++######################+++++++'  
    `````````;;;';;;;                           ''++++++++++####++++++++++++++++++++++++++++++++++##++++++++###########+++++###########################+++++''  
         `````````';;;;```';                       '+++++++++++++++++++++++++++++++++++++++++++++++++++++######++++###################################+++++'    
              ;;;;;:;;;;;``````';                    ;;'+++++++++++++++++++++++++++++++++++++++++++++++#####++++++########+#####++#++#++#############+++++'     
                   ;````````````;;;;;;;;;;;;;;;`````````;;;'++++++++++++++++++++++++++++++++++++++++++######++++++++++++++++++++++++##++############++++''      
                         ```;;;:;;;;```'';;;;;;;;;;;;;`````````++++++++#########################+++++##+####################+###+++#+###++#######+++#+''        
                             ;;'+'';;'';;;;;;;;;;;::::;;;;;::;;:;;'++++++######################++++++++++++###################+#####++++++######++++'           
                                     ```;;;;;;::::::;;;;;:;;;;;;;;;::;++++++#################++++++++++############################++++######+++++'             
                                             ```++';;::::```+;;;;'++:;;:;'++###############+####+++++###########################++++###+##+++'                  
                                                   ;```;;';;;;;;;;++;;;:;';+###################+######++++++#####+'+```+++++``````''                            
                                                      ;:'+;;;;;:;++;;';;++'+++######################+++##+'+'';'+;::':,,:;                                      
                                                     :::;+++++++'';;';;+########################'+##+'+#+''+#+''++';++;:';,                                     
                                                     ;;:;;;;;``````'++++#######################++###+'+##+'+#+++##++#++'+'::;'                                  
                                                     +';;```++++++#++++##################++#########+'++++'+#+++#+++#+++++';;,;'+;;                             
                                                   ''+++'+++++++++++########+#######################+++#+++##+++++++#+++#++++'+++++'                            
                                                   '+#+'+++####################################+###################################+'                           
                                                       '  '++######++#''++#####################+++######################+++++```                                
                                                                           '++    '+#######++     '                                                             
                                                                            ''     ' ``````'                                                                    
                                                                            '     ''     ''                                                                     
                                                                            ''                                                                                  
                                        @@@   @@@                                            @@ @@@   @@@              @@                  #@                   
                                        @@@  +@@@                                           +@  @@@  +@@@          @@  @@                   @#                  
                                        @@@  @#@@                                           @@  @@@  @#@@          @@  @@                   @@                  
                                        @@@  @`@@  +@@@@+  '@@@@,  @@  @@  @@@@ '@@@@+     +@'  @@@  @,@@  +@@@@+ @@@@ @@+@@@  @@ @@ #@@@@   @+                 
                                        @@@+ @ @@  @@''@@  @@'+@@  @@  @@  @@@@ @@+'@@     @@   @@@+ @ @@  @@''@@  @@  @@@ @@# @@@@@ @@'#@#  @@                 
                                        @@@@ @ @@ #@+  +@# @@+     @@  @@  @@      '@@     @@   @@@@ @ @@ #@+  +@# @@  @@' `@@ @@+      #@@  @@                 
                                        @@+@#@ @@ @@    @@  @@@@@  @@  @@  @@   @@@@@@     @@   @@+@#@ @@ @@    @@ @@  @@   @@ @@    @@@#@@  @@                 
                                        @@ @@# @@ +@#  #@+ @@  @@  @@  @@  @@   @@  @@     @@   @@ @@# @@ +@#  #@+ @@  @@   @@ @@   #@  +@@  @@                 
                                        @@ @@  @@  @@@@@@  @@@@@@  @@@@@@  @@   @@@@@@     @@   @@ @@  @@  @@@@@@  @@@ @@   @@ @@   #@@@@@@  @@                 
                                        @@ @@  @@   @@@@    @@@@'  #@@+@@  @@   #@@##@     '@'  @@ @@  @@   @@@@   @@@ @@   @@ @@    @@@ @@ '@+                 
                                                                                            @@                                              @@                  
                                                                                            +@                                              @#                  
                                                                                             @@                                            #@                   
Osaka - Mosura - Special Thanks: The HySDS Team
'''
    print(moth)


if __name__ == "__main__":
    '''
    Osaka CLI
    '''
    sys.exit(main())
