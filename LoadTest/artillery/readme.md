To install
```bash
npm install -g artillery
or
npm install artillery
```

To run a quick test
```bash
artillery quick --count 10 -n 20 https://netsys.uno
.\node_modules\artillery\bin\run quick -k --count 100 -n 60 https://192.168.1.250:443
.\node_modules\artillery\bin\run run .\home-xylon.yml

```

To generate html report
```bash
artillery quick --count 10 -n 20 https://netsys.uno -o result.json
.\node_modules\artillery\bin\run quick -k --count 100 -n 60 https://192.168.1.250:443 -o result.json
.\node_modules\artillery\bin\run run .\home-xylon.yml -o result.json
.\node_modules\artillery\bin\run report result.json
open result.json.html
```


