# Python-Obfuscator

One night I got bored of writing good code, so I made good code to make bad code.

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/davidteather/python-obfuscator?style=flat-square)](https://github.com/davidteather/TikTok-Api/releases) [![Downloads](https://static.pepy.tech/personalized-badge/python_obfuscator?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads)](https://pypi.org/project/python_obfuscator/) ![](https://visitor-badge.laobi.icu/badge?page_id=davidteather.python-obfuscator) [![Linkedin](https://img.shields.io/badge/LinkedIn-0077B5?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/david-teather-4400a37a/) 


Consider sponsoring me [here](https://github.com/sponsors/davidteather)

## Installing

```
pip install python_obfuscator
```

## Quickstart

Print out obfuscated code
```
pyobfuscator -i your_file.py
```

Apply changes to the input file
```
pyobfuscator -i your_file.py -r True
```

## More Detailed Documentation

You can use this as a module if you want
```
import python_obfuscator
obfuscator = python_obfuscator.obfuscator()

code_to_obfuscate = "print('hello world')"
```

You can also exclude certain techniques applied for obfuscation
```
import python_obfuscator
from python_obfuscator.techniques import add_random_variables
obfuscator = python_obfuscator.obfuscator()

code_to_obfuscate = "print('hello world')"
obfuscated_code = obfuscator.obfuscate(code_to_obfuscate, remove_techniques[add_random_variables])
```
Find a list of all techniques [here](https://github.com/davidteather/python-obfuscator/blob/main/python_obfuscator/utilities.py)

## Example Obfuscated Code

Input
```
y = input("what's your favorite number")

user_value = int(y)
print("{} that's a great number!".format(user_value))
```

[With `pyobfuscate -i file.py`](https://gist.github.com/davidteather/b6ff932140d8c174b9c6f50c9b42fdaf)


[With `--one-liner True`](https://gist.github.com/davidteather/75e48c04bf74f0262fe2919239a74295)


## Built With

* [Python 3.7](https://www.python.org/) - The web framework used

## Authors

* **David Teather** - *Initial work* - [davidteather](https://github.com/davidteather)

See also the list of [contributors](https://github.com/davidteather/TikTok-Api/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details