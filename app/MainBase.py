from app.settings import *
from app.RGI import RGI
import argparse
from app.ConvertRGIJsonToTSV import ConvertJsonToTSV
from app.Galaxy import Galaxy
import app.Parser
import app.load
import app.clean
import app.card_annotation
import app.wildcard_annotation
import app.remove_duplicates
from app.BWT import BWT
from app.Heatmap import Heatmap

class MainBase(object):
    def __init__(self, api=False):
        # """
        self.cpu_count = os.cpu_count()
        USAGE='''%(prog)s <command> [<args>]
            commands are:
               main     Runs rgi application
               tab      Creates a Tab-delimited from rgi results
               parser   Creates categorical .json files RGI wheel visualization. An input .json file containing the RGI results must be input.
               load     Loads CARD database json file
               clean    Removes BLAST databases and temporary files
               galaxy   Galaxy project wrapper
               bwt      Metagenomics resistomes (Experimental)
               card_annotation create fasta files with annotations from card.json (Experimental)
               wildcard_annotation create fasta files with annotations from variants (Experimental)
               remove_duplicates removes duplicate sequences (Experimental)
               heatmap  heatmap for multiple analysis (Experimental)
               database Information on installed card database'''

        parser = argparse.ArgumentParser(prog="rgi", description='{} - {}'.format(APP_NAME, SOFTWARE_VERSION), epilog=SOFTWARE_SUMMARY, usage=USAGE)
        parser.add_argument('command', choices=['main', 'tab', 'parser', 'load',
                                                'clean', 'galaxy', 'database', 'bwt', 'card_annotation', 'wildcard_annotation', 'remove_duplicates', 'heatmap'],
                                                help='Subcommand to run')

        if api == False:
            args=parser.parse_args(sys.argv[1:2])
            # """
            if not hasattr(self, args.command):
                logger.info("Unrecognized command: {}".format(args.command))
                # parser.print_help()
                exit("Error: Unrecognized command: {}".format(args.command))
            getattr(self, args.command)()

    def main(self):
        parser = self.main_args()
        args = parser.parse_args(sys.argv[2:])
        self.main_run(args)

    def main_args(self):
        parser = argparse.ArgumentParser(prog="rgi main",description="{} - {} - Main".format(APP_NAME,SOFTWARE_VERSION))
        parser.add_argument('-i','--input_sequence', dest="input_sequence", required=True, \
            help='input file must be in either FASTA (contig and protein), FASTQ(read) or gzip format! e.g myFile.fasta, myFasta.fasta.gz')
        parser.add_argument('-o','--output_file', dest="output_file", required=True, help="output folder and base filename")
        parser.add_argument('-t','--input_type', dest="input_type",
                type=str.lower,
                default="contig", choices=['read','contig','protein', 'wgs'],
                required=False,
                help='specify data input type (default = contig)')
        parser.add_argument('-a','--alignment_tool', dest="aligner",
                type=str.upper,
                choices = ['DIAMOND', 'BLAST'],
                default="BLAST",
                help = "specify alignment tool (default = BLAST)")
        parser.add_argument('-n','--num_threads', dest="threads", type=int,
                default=self.cpu_count, help="number of threads (CPUs) to use in the BLAST search (default={})".format(self.cpu_count))
        parser.add_argument('--include_loose', dest="loose", action='store_true', help="include loose hits in addition to strict and perfect hits")
        parser.add_argument('--local', dest="local_database", action='store_true', help="use local database (default: uses database in executable directory)")
        parser.add_argument('--clean', dest="clean", action="store_true", help="removes temporary files")
        parser.add_argument('--debug', dest="debug", action="store_true", help="debug mode")
        parser.add_argument('--low_quality', dest="low_quality", action="store_true", help="use for short contigs to predict partial genes")
        parser.add_argument('-d','--data', dest="data", default="NA",
                choices=['wgs', 'plasmid', 'chromosome', 'NA'],
                help = "specify a data-type (default = NA)")
        parser.add_argument('-v','--version', action='version', version="{}".format(SOFTWARE_VERSION), help = "prints software version number")
        return parser

    def main_run(self, args):
        rgi_obj = RGI(**vars(args))
        rgi_obj.run()

    def tab(self):
        parser = self.tab_args()
        args = parser.parse_args(sys.argv[2:])
        self.tab_run(args)

    def tab_args(self):
        parser = argparse.ArgumentParser(prog="rgi tab", description="{} - {} - Tab-delimited".format(APP_NAME, SOFTWARE_VERSION))
        parser.add_argument('-i', '--afile', help='must be a rgi json result file', required=True)
        return parser

    def tab_run(self, args):
        obj = ConvertJsonToTSV(args.afile)
        obj.run()

    def parser(self):
        parser = self.parser_args()
        args = parser.parse_args(sys.argv[2:])
        self.parser_run(args)

    def parser_args(self):
        parser = app.Parser.create_parser()
        return parser

    def parser_run(self, args):
        app.Parser.api_main(args)

    def load(self):
        parser = self.load_args()
        args = parser.parse_args(sys.argv[2:])
        self.load_run(args)

    def load_args(self):
        parser = app.load.create_parser()
        return parser

    def load_run(self, args):
        app.load.main(args)

    def card_annotation(self):
        parser = self.card_annotation_args()
        args = parser.parse_args(sys.argv[2:])
        self.load_run(args)

    def card_annotation_args(self):
        parser = app.card_annotation.create_parser()
        return parser

    def card_annotation_run(self, args):
        app.card_annotation.main(args)

    def wildcard_annotation(self):
        parser = self.wildcard_annotation_args()
        args = parser.parse_args(sys.argv[2:])
        self.load_run(args)

    def wildcard_annotation_args(self):
        parser = app.wildcard_annotation.create_parser()
        return parser

    def wildcard_annotation_run(self, args):
        app.wildcard_annotation.main(args)

    def remove_duplicates(self):
        parser = self.remove_duplicates_args()
        args = parser.parse_args(sys.argv[2:])
        self.load_run(args)

    def remove_duplicates_args(self):
        parser = app.remove_duplicates.create_parser()
        return parser

    def remove_duplicates_run(self, args):
        app.remove_duplicates.main(args)

    def bwt(self):
        parser = self.bwt_args()
        args = parser.parse_args(sys.argv[2:])
        self.bwt_run(args)

    def bwt_args(self):
        parser = argparse.ArgumentParser(prog="rgi bwt",description='Aligns metagenomic reads to CARD and wildCARD reference using bowtie or bwa and provide reports.')
        parser.add_argument('-1', '--read_one', required=True, help="raw read one (qc and trimmied)")
        parser.add_argument('-2', '--read_two', help="raw read two (qc and trimmied)")
        parser.add_argument('-a', '--aligner', default="bowtie2", choices=['bowtie2','bwa'], help="aligner")
        parser.add_argument('-n','--threads', dest="threads", type=int,default=self.cpu_count, help="number of threads (CPUs) to use (default={})".format(self.cpu_count))
        parser.add_argument('-o','--output_file', dest="output_file", required=True, help="name of output filename(s)")
        parser.add_argument('--debug', dest="debug", action="store_true", help="debug mode")
        parser.add_argument('--local', dest="local_database", action='store_true', help="use local database (default: uses database in executable directory)")
        parser.add_argument('--include_wildcard', dest="include_wildcard", action="store_true", help="include wildcard")
        return parser

    def bwt_run(self, args):
        obj = BWT(
            args.aligner,
            args.include_wildcard,
            args.read_one,
            args.read_two,
            args.threads,
            args.output_file,
            args.debug,
            args.local_database
        )
        obj.run()

    def heatmap(self):
        parser = self.heatmap_args()
        args = parser.parse_args(sys.argv[2:])
        self.heatmap_run(args)

    def heatmap_args(self):
        parser = argparse.ArgumentParser(prog="rgi heatmap",description='Creates a heatmap when given multiple RGI results.')
        parser.add_argument('-i', '--input', dest="input", required=True, help="Directory containing the RGI .json files (REQUIRED)")
        parser.add_argument('-category', dest="classification", choices=("drug_class", "resistance_mechanism", "gene_family"), help="The option to organize models based on a category (OPTIONAL)")
        parser.add_argument('-frequency', dest="frequency", choices=("on", "off"), default="off", help="Represent samples based on resistance profile. Default = off (OPTIONAL)")
        parser.add_argument('-o', '--output', dest="output", default="RGI_heatmap", help="Name for the output .eps file (OPTIONAL). The number of files run will automatically be appended to the end of the file name.")
        parser.add_argument('-cluster', dest="cluster", choices=("samples", "genes", "both"),help="Option to use SciPy's hiearchical clustering algorithm to cluster rows (AMR genes) or columns (samples) (OPTIONAL)")
        parser.add_argument('-display', dest="display", choices=("plain", "fill", "text"), default="plain", help="Specify display options for categories (OPTIONAL).")
        parser.add_argument('--debug', dest="debug", action="store_true", help="debug mode")

        return parser

    def heatmap_run(self, args):
        obj = Heatmap(args.input, args.classification, args.frequency, args.output, args.cluster, args.display, args.debug)
        obj.run()

    def clean(self):
        parser = self.clean_args()
        args = parser.parse_args(sys.argv[2:])
        self.clean_run(args)

    def clean_args(self):
        parser = app.clean.create_parser()
        return parser

    def clean_run(self, args):
        app.clean.main(args)

    def galaxy(self):
        parser = self.galaxy_args()
        args = parser.parse_args(sys.argv[2:])
        self.galaxy_run(args)

    def galaxy_args(self):
        parser = argparse.ArgumentParser(prog="rgi galaxy", description="{} - {} - Galaxy project wrapper".\
            format(APP_NAME, SOFTWARE_VERSION))
        parser.add_argument('--galaxy_database', help='specify path to CARD blast databases. Note this is \
            ONLY used for galaxyproject wrapper (default: None)', required=False)
        parser.add_argument('--debug', dest="debug", action="store_true", help="debug mode")
        return parser

    def galaxy_run(self, args):
        obj = Galaxy(args.galaxy_database)
        obj.load_db_galaxy()

    def database(self):
        parser = self.database_args()
        args = parser.parse_args(sys.argv[2:])
        print(self.database_run(args))

    def database_args(self):
        parser = argparse.ArgumentParser(prog="rgi database", description="{} - {} - Database".format(APP_NAME, SOFTWARE_VERSION))
        parser.add_argument('-v','--version',action='store_true', help = "prints data version number")
        parser.add_argument('--local', dest="local_database", action='store_true', help="use local database (default: uses database in executable directory)")
        return parser

    def database_run(self, args):
        data_version = ""
        # path to card.json file and database files
        if args.local_database:
            db = LOCAL_DATABASE
            # error if it doesn't exist
            if not os.path.exists(LOCAL_DATABASE):
                print("Error: missing local directory: {}".format(LOCAL_DATABASE))
                print("Please run `rgi load --local -i <path to card.json>` to create local database.")
                print("See `rgi load --help` to upload the card.json to rgi application.\n".format(os.path.abspath(LOCAL_DATABASE)))
                exit()
        else:
            db = data_path
        card_json_path = os.path.join(db,"card.json")
        if os.path.isfile(card_json_path) == True:
            with open(card_json_path) as json_file:
                json_data = json.load(json_file)
                for item in json_data.keys():
                    if item == "_version":
                        data_version = json_data[item]
        if data_version == "":
            # logger.error('data file card.json not found in data path: {}. \nPlease download card.json from https://card.mcmaster.ca/download. \nSee `rgi load --help` to upload the card.json to rgi application.\n'.format(os.path.abspath(db)))
            print('\nError: data file card.json not found in data path: {}. \nPlease download card.json from https://card.mcmaster.ca/download. \nSee `rgi load --help` to upload the card.json to rgi application.\n'.format(os.path.abspath(db)))
        return data_version

if __name__ == '__main__':
    MainBase()
