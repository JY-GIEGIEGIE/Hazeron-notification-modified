# 来自钉钉机器人的浙江大学信息全搜集

## Usage

use

```shell
pip install -r requirements.txt
```

to install all the requirements.

configurations are in the directory `config`, and make a directory named `storage` to storage previous data.

write `config/secret_config.json`

```json
{
    "WEBHOOK": "",
    "SECRET": "",
    "WEBVPN_NAME": "",
    "WEBVPN_SECRET":
}
```

and run

```shell
python main.py
```
