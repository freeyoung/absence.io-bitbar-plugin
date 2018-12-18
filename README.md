# A BitBar plugin for absence.io time tracking

## Howto

### Install BitBar

Go to [getbitbar.com](https://getbitbar.com) and follow the instructions there.

Probably you will see some other plugins interesting to you.

### Install dependencies

```
$ brew install python3
$ pip3 install requests mohawk python-dateutil
```

### Prepare the config file

```
$ cp .absence.example.cfg ~/.absence.cfg
$ vim ~/.absence.cfg
```

### Copy the plugin to your BitBar plugin directory

For me it's `~/.bitbar`, so:

```
$ cp absence.30s.py ~/.bitbar/absence.30s.py
```

### Launch BitBar.app

![Looks like this](https://raw.githubusercontent.com/freeyoung/absence.io-bitbar-plugin/master/absence.png)
