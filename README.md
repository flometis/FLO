FLO è una web app per aiutare la pubblica amministrazone a scrivere comunicati per il pubblico in lingua facile, evitando le forme tipiche del burocratese.

Si può provare Facile da Leggere Online dal suo indirizzo ufficiale:
https://faciledaleggere.online/flo/

## Architettura
FLO è una app web con frontend in HTML5+JS e backend in Python3. Le due parti dell'applicazione sono pubblicate ciascuna in un container docker, per garantire la replicabilità. Utilizzando docker-compose è possibile creare e avviare i container: sono necessarie piccole modifiche dopo la creazione, soprattutto per il backend. I comandi sono inseriti nello script **deploy.sh**. Questo script può essere utilizzato anche per aggiornare l'applicazione dopo un git pull. Lo script si occupa anche dell'aggiornamento di Bran, direttamente dal suo repository.

Il backend genera dei file temporanei, dentro il suo container, per le analisi dei testi. È presente un cronjob che pulisce i file più vecchi di 30 minuti.

### Configurazione Apache

Per rendere pubblica l'applicazione bisogna avere un reverse proxy che punti al container di frontend per la location /flo/ e al container di backend per /floapi. Se si utilizza un Apache esterno a Docker si può fare così:
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
Nel repository è presente un file con una configurazione funzionante.
Questo permette di tenere chiuse sull'host le porte 8001 e 8002 per tutte le interfacce che non siano **lo**, così le richieste dovranno passare dal webproxy.

Se si utilizza un webproxy dockerizzato, si può direttamente far puntare ciascuna location alla porta 80 dei container, se appartiene alla **public_net**.

### Requisiti minimi
I requisiti minimi della macchina virtuale per far girare i container sono:
* Ubuntu 18.04 con Docker 20.10 e docker-compose 1.28
* 1CPU
* 1GB di RAM
* 1GB di spazio libero

### Dipendenze
Tutte le dipendenze sono gestite dai Dockerfile, i container dovrebbero essere autonomi. Nel container di backend viene installato Bran, prelevando l'ultima versione dal ramo di sviluppo (ramo **dev**) del repository. È necessario mantenere Bran sul ramo di sviluppo, perché il ramo stabile manca di molte caratteristiche necessarie per FLO.
Il parser utilizzato è udpipe, perché più leggero e perché supporta diversi modelli lingusitici. Volendo utilizzare Tint, sarà necessaria molta più RAM (2GB solo per Tint) e provvedere all'avvio del server Tint. Per il resto basta modificare il codice di FLO per eseguire l'importazione in Bran da Tint invece che da Udpipe. Per il resto, il codice può rimanere lo stesso. 

## TODO
FLO è ancora in fase di sviluppo, anche se ormai buona parte del progetto è stata implementata. Attualmente è ancora necessario implementare almeno queste funzioni:
- [ ] Statistiche su parole del Vocabolario di Base
- [ ] Download dei file generati da Bran

## Il funzionamento di FLO
FLO è stato progettato per lavorare su testi in lingua italiana a tema burocratico. Può essere possibile modificarlo per lavorare su altre lingue, tra quelle permesse da Udpipe e Bran. Inoltre, si possono scrivere altre regole, semplicemente ricordandosi di aggiungere il loro caricamento.
Le parti di testo da correggere vengono identificate grazie a delle regole (ruleset) definite nei file tsv presenti in questo repository (es: backend/files/filters_etr.tsv). Queste regole possono essere semplici espressioni regolari sulle forme grafiche (le parole del testo così come sono scritte) oppure filtri di Bran (che quindi possono verificare anche il lemma, il tag pos, o la morfologia).

