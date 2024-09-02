from logging.config import dictConfig
from flask import Flask
import tomli

def setup_logging(config):
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': config.get('level', 'INFO')
            }
        },
        'root': {
            'handlers': ['console'],
            'level': config.get('level', 'INFO')
        }
    }
    dictConfig(log_config)

def load_config(app: Flask):
    with open('config.toml', 'rb') as f:
        config = tomli.load(f)
        app.config.update(config['flask'])
        logging_config = config.get('logging', {})
        setup_logging(logging_config)
        app.config['DATABASE_URI'] = config['database']['uri']
        app.name = config['flask'].get('name', 'xNode')


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    load_config(app)
    server_config = app.config.get('server', {})
    host = server_config.get('host', '127.0.0.1')
    port = server_config.get('port', 5000)
    app.run(host=host, port=port, debug=app.config['debug'])