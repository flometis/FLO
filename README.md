FLO è una web app per aiutare la pubblica amministrazone a scrivere comunicati per il pubblico in lingua facile, evitando le forme tipiche del burocratese.

## Architettura
FLO è una app web con frontend in HTML5+JS e backend in Python3.


## Ambiente di staging
https://bianconiglio.cloud/flo/

### Configurazione Apache

```
<Location /flo/>
    ProxyPass http://127.0.0.1:8001/
    ProxyPassReverse http://127.0.0.1:8001/
    ProxyAddHeaders On
    ProxyPreserveHost On
</Location>

<Location /floapi>
    ProxyPass http://127.0.0.1:8002/correct
    ProxyPassReverse http://127.0.0.1:8002/correct
    ProxyAddHeaders On
    ProxyPreserveHost On
</Location>
```

