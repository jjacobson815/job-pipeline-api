<a id="module-app.core.config"></a>

<a id="app-core-config-module"></a>

# app.core.config module

Application configuration via Pydantic BaseSettings.

Reads from environment variables and .env files. All secrets and service
URLs are validated at startup — a missing or malformed value crashes fast
rather than failing silently at runtime.

### *class* app.core.config.Settings(\_case_sensitive: bool | None = None, \_nested_model_default_partial_update: bool | None = None, \_env_prefix: str | None = None, \_env_prefix_target: EnvPrefixTarget | None = None, \_env_file: DotenvType | None = WindowsPath('.'), \_env_file_encoding: str | None = None, \_env_ignore_empty: bool | None = None, \_env_nested_delimiter: str | None = None, \_env_nested_max_split: int | None = None, \_env_parse_none_str: str | None = None, \_env_parse_enums: bool | None = None, \_cli_prog_name: str | None = None, \_cli_parse_args: bool | list[str] | tuple[str, ...] | None = None, \_cli_settings_source: CliSettingsSource[Any] | None = None, \_cli_parse_none_str: str | None = None, \_cli_hide_none_type: bool | None = None, \_cli_avoid_json: bool | None = None, \_cli_enforce_required: bool | None = None, \_cli_use_class_docs_for_groups: bool | None = None, \_cli_exit_on_error: bool | None = None, \_cli_prefix: str | None = None, \_cli_flag_prefix_char: str | None = None, \_cli_implicit_flags: bool | Literal['dual', 'toggle'] | None = None, \_cli_ignore_unknown_args: bool | None = None, \_cli_kebab_case: bool | Literal['all', 'no_enums'] | None = None, \_cli_shortcuts: Mapping[str, str | list[str]] | None = None, \_secrets_dir: PathType | None = None, \_build_sources: tuple[tuple[PydanticBaseSettingsSource, ...], dict[str, Any]] | None = None, , app_name: str = 'Job Pipeline API', app_version: str = '0.1.0', environment: Literal['development', 'staging', 'production'] = 'development', debug: bool = False, log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO', teal_api_key: Annotated[str, MinLen(min_length=10)], openai_api_key: Annotated[str, MinLen(min_length=10)], redis_url: RedisDsn = 'redis://localhost:6379/0', teal_base_url: HttpUrl = 'https://api.teal.dev/v1', openai_base_url: HttpUrl = 'https://api.openai.com/v1', http_timeout_seconds: Annotated[float, Gt(gt=0)] = 30.0, http_max_retries: Annotated[int, Ge(ge=0)] = 3, http_backoff_base: Annotated[float, Gt(gt=0)] = 1.0, celery_task_default_queue: str = 'pipeline', celery_task_acks_late: bool = True, celery_worker_prefetch_multiplier: int = 1)

Bases: `BaseSettings`

Immutable, validated configuration singleton.

#### app_name *: str*

#### app_version *: str*

#### celery_task_acks_late *: bool*

#### celery_task_default_queue *: str*

#### celery_worker_prefetch_multiplier *: int*

#### debug *: bool*

#### environment *: Literal['development', 'staging', 'production']*

#### http_backoff_base *: float*

#### http_max_retries *: int*

#### http_timeout_seconds *: float*

#### log_level *: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']*

#### model_config *= {'arbitrary_types_allowed': True, 'case_sensitive': False, 'cli_avoid_json': False, 'cli_enforce_required': False, 'cli_exit_on_error': True, 'cli_flag_prefix_char': '-', 'cli_hide_none_type': False, 'cli_ignore_unknown_args': False, 'cli_implicit_flags': False, 'cli_kebab_case': False, 'cli_parse_args': None, 'cli_parse_none_str': None, 'cli_prefix': '', 'cli_prog_name': None, 'cli_shortcuts': None, 'cli_use_class_docs_for_groups': False, 'enable_decoding': True, 'env_file': '.env', 'env_file_encoding': 'utf-8', 'env_ignore_empty': False, 'env_nested_delimiter': None, 'env_nested_max_split': None, 'env_parse_enums': None, 'env_parse_none_str': None, 'env_prefix': '', 'env_prefix_target': 'variable', 'extra': 'ignore', 'json_file': None, 'json_file_encoding': None, 'nested_model_default_partial_update': False, 'protected_namespaces': ('model_validate', 'model_dump', 'settings_customise_sources'), 'secrets_dir': None, 'toml_file': None, 'validate_default': True, 'yaml_config_section': None, 'yaml_file': None, 'yaml_file_encoding': None}*

Configuration for the model, should be a dictionary conforming to [ConfigDict][pydantic.config.ConfigDict].

#### openai_api_key *: str*

#### openai_base_url *: HttpUrl*

#### redis_url *: RedisDsn*

#### *property* redis_url_str *: str*

Return the Redis DSN as a plain string for libraries that refuse AnyUrl.

#### teal_api_key *: str*

#### teal_base_url *: HttpUrl*

### app.core.config.get_settings() → [Settings](#app.core.config.Settings)

Return a cached Settings instance (parsed once per process).
