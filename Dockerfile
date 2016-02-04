## Start with the official rocker image providing 'base R'
FROM rocker/rstudio:latest
## This handle reaches Torsten
MAINTAINER "Torsten Steinbach" torsten@de.ibm.com

COPY supervisor.conf /supervisor.conf
COPY install.R /install.R

## Install some system commands
## Install ibmdbR and RODBC from CRAN
## Download IBM data server package, install it and set up odbc.ini
RUN rm -rf /var/lib/apt/lists/ \
  && apt-get update \
  && apt-get -y install procps \
  && apt-get -y install unixodbc-dev \
  && apt-get -y install ksh \
  && apt-get -y install ssh \
  && R -f /install.R \
  && wget ftp://db2ftp.torolab.ibm.com//devinst/db2_v105fp7/linux64/s151221/v10.5fp7_linux64_dsdriver.tar.gz \
  && tar -xvzf v10.5fp7_linux64_dsdriver.tar.gz \
  && dsdriver/installDSDriver \
  && printf "[DASHDB]\nDriver = /dsdriver/lib/libdb2o.so\n" >> /etc/odbc.ini \
  && adduser rstudio sudo \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/

## Add ssh deamon to startup sequence
RUN cat /supervisor.conf >> /etc/supervisor/conf.d/supervisord.conf
