import logging

from django.core.management import BaseCommand, call_command, CommandError


logger = logging.getLogger("django-elastic-migrations")


class Command(BaseCommand):
    help = "django-elastic-migrations: base command for search index management"

    MODE_INDEXES = 'index'
    MODE_VERSIONS = 'version'

    def __init__(self):
        super(Command, self).__init__()
        print ""

    def add_arguments(self, parser):
        parser.add_argument(
            "-ls", "--list-available", action='store_true',
            help='List the available named indexes; calls es_list'
        )
        parser.add_argument(
            "--create", action='store_true', default=False,
            help='Create the named index; calls es_create'
        )
        parser.add_argument(
            "--update", action='store_true', default=False,
            help='Update the named index; calls es_update'
        )
        parser.add_argument(
            "--drop", action='store_true', default=False,
            help='Drop the named index, calls es_drop'
        )
        parser.add_argument(
            "--activate", action='store_true', default=False,
            help='Activate the latest version of the named index; calls es_activate'
        )

    def handle(self, *args, **options):
        if 'list_available' in options:
            call_command('es_list', *args, **options)
        for cmd in ['create', 'update', 'activate', 'drop']:
            if cmd in options:
                return call_command("es_{}".format(cmd), *args, **options)

    """
    Methods To Specify Indexes
    The methods below are added as an aid to subcommands
    so indexes or index versions are specified in a unified way.
    """

    def get_index_specifying_help_messages(self):
        """
        Override in subclasses to customise the messages as necessary
        """
        return {
            "mode": "Specify whether to operate on indexes or index versions",
            "index": (
                "Depending on --mode, the name of index(es) or index version(s) "
                "to operate on. In the case of `--mode {mode_indexes}` (the default), "
                "the active version will be operated upon, and indexes without an "
                "active version will be ignored.".format(mode_indexes=self.MODE_INDEXES)
            ),
            "all": (
                'Operate on all of the active indexes or index versions, depending on '
                'whether `--mode {mode_index}`, or `--mode {mode_version}` is '
                'supplied.'.format(mode_index=self.MODE_INDEXES, mode_version=self.MODE_VERSIONS)
            )
        }

    def get_index_version_specifying_arguments(self, parser):
        messages = self.get_index_specifying_help_messages()
        parser.add_argument(
            "--mode",
            help=messages.get("mode"),
            choices=[self.MODE_INDEXES, self.MODE_VERSIONS],
            default=self.MODE_INDEXES
        )

    def get_index_specifying_arguments(self, parser, include_versions=True):
        messages = self.get_index_specifying_help_messages()
        parser.add_argument(
            'index', nargs='*',
            help=messages.get("index")
        )

        if include_versions:
            # some arguments do not allow specifying index versions,
            # such as es_create. In that case, do not include this arg.
            self.get_index_specifying_arguments(parser)

        parser.add_argument(
            "--all", action='store_true', default=False,
            help=messages.get("all")
        )

    def get_index_specifying_options(self, options):
        mode = options.get('mode', self.MODE_INDEXES)
        indexes = options.get('index', [])
        use_version_mode = mode == self.MODE_VERSIONS
        apply_all = options.get('all', False)

        if apply_all:
            if indexes:
                logger.warning(
                    "./manage.py es_clear --all received named indexes "
                    "'{}': these specified index names will be ignored "
                    "because you have requested to clear *all* the "
                    "indexes.".format(", ".join(indexes))
                )

        if not (indexes or apply_all):
            raise CommandError(
                "At least one {mode} or --all must be specified".format(
                    mode=mode
                ))
        return indexes, use_version_mode, apply_all


ESCommand = Command
