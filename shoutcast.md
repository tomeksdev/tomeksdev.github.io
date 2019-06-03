**Shoutcast instalacija:**


**KORAK 1:**

  * Potrebno je napraviti virtualnu mašinu sa ***4GB rama***, ***2xCPU***, mreža mora biti u ***309 Users Public***, te hard disk od ***30GB***. Kada se kreira virtualka instalirati ***Ubuntu 18.04 x64 server*** te napraviti ***sudo apt update && sudo apt upgrade***. Nakon toga sljediti upute ispod za instalaciju Shoutcast servera.


**KORAK 2:**  

  * Najlakša instalacija je pomoću skripte za automatsku instalaciju koja se nalazi na https://github.com/tomeksdev/tomeksdev.github.io/raw/master/tools/linux/shoutcast-inst.tar.gz
  * Skine se scripta te se ukucaju sljedeće naredbe:

<code>wget https://github.com/tomeksdev/tomeksdev.github.io/raw/master/tools/linux/shoutcast-inst.tar.gz
tar xfz shoutcast-inst.tar.gz
sudo ./shoutcast-inst</code>


**KORAK 3:**

  * Kada je instalacija završena potrebno je samo editirati ***sc_serv.conf*** file:

<code>sudo nano /shoutcast/sc_serv.conf</code>

**KORAK 4:**

  * Kada je konfiguracija završena, potrebno je s komandom shoutcast pokrenuti servis:

<code>sudo shoutcast start</code>

Također postoje i još dvije komande sa to su ***shoutcast stop*** i ***shoutcast restart***.


===== Korak po korak: =====

**KORAK 1:**

  * Ako se želi shoutcast instalirati ručno i korak po korak, sljedi upute dolje. Potrebno je skinuti shoutcast server sa njihove glavne stranice:

<code>cd /
mkdir shoutcast
cd /shoutcast
wget https://download.nullsoft.com/shoutcast/tools/sc_serv2_linux_x64-latest.tar.gz</code>

**KORAK 2:**

  * Nakon toga je potrebno extract-ati skinuti file te složiti ***shoutcast*** folder i kopirati sve iz sc_serv foldera gdje smo extract-ali u taj shoutcast folder

<code>tar xfz sc*
rm sc_serv2_linux_x64-latest.tar.gz</code>

**KORAK 3:**

  * Kada smo sve kreirali, potrebo je napraviti config file koji sadrži konfiguraciju za shoutcast server.

<code>nano sc_server.conf</code>

  * Unutar tog config file-a napisati ove linije za konfiguraciju:

<code>adminpassword=password
password=password1
requirestreamconfigs=1
streamadminpassword_1=password2
streamid_1=1
streampassword_1=password3
streampath_1=http://ServerIP:8000
logfile=logs/sc_serv.log
w3clog=logs/sc_w3c.log
banfile=control/sc_serv.ban
ripfile=control/sc_serv.rip</code>

  * Zamjeniti sve ***password*** sa željenom lozinkom te zamjeniti ***ip***, te ***port*** ako je to potrebno.

**KORAK 5:** 

  * Nakon toga spremiti konfiguraciju te dodati privilegije file-u ***sc_serv***.

<code>chmod +x sc_serv</code>

**KORAK 6(ukoliko nema unutar shoutcast foldera cacert.pem datoteke):**

  * Prije nego pokrenemo server, potrebno je i skinuti DDNAS certifikat da server radi i u v1 i v2 verziji shoutcast-a

<code>cd /shoutcast
wget http://curl.haxx.se/ca/cacert.pem</code>

**KORAK 7:**

  * Naredba za pokretanje shoutcast servera:

<code>cd /shoutcast/
./sc_server &</code>



**Nakon instalacije, po potrebi:**

  * Nakon pokretanja servera se može pristupati shoutcast applikaciji pomoćiu browsera i nekog streaming toola gdje se vide svi podaci i statistike.
<code>URL: http://ServerIP:port (default 8000)</code>

  * Ponekad je potrebno i posložiti hostname, pa se to može podesiti na našim DNS serverima

  * Za pokretanje shoutcast server automatski nakon svakog reboota ili gašenja i paljenja servera skinete ovu scriptu https://github.com/tomeksdev/tomeksdev.github.io/raw/master/tools/linux/shoutcast-cmd.tar.gz te ju extract-ate i upišete naredbe redom.

<code>tar xfz shoutcast-cmd.tar.gz
sudo cp /shoutcast-cmd /usr/bin/shoutcast
rm shoutcast-cmd.tar.gz && rm shoutcast-cmd
sudo cp /shoutcast /etc/init.d/
sudo cp /shoutcast /etc/rc3.d/S08shoutcast
rm shoutcast
</code>

