@ECHO OFF
IF NOT "%1" == "" (
    python -c "if __name__ == '__main__': import pycnbi.decoder.trainer as m; m.config_run('%1')"
) ELSE (
    ECHO Usage: %0 [CONFIG_FILE]
)
