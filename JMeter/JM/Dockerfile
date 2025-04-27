FROM openjdk:11-slim

# Set environment variables
ENV JMETER_VERSION=5.5
ENV JMETER_HOME=/opt/apache-jmeter-${JMETER_VERSION}
ENV PATH=$JMETER_HOME/bin:$PATH

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip && \
    apt-get clean

# Download and install JMeter
RUN wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-${JMETER_VERSION}.tgz && \
    tar -xzf apache-jmeter-${JMETER_VERSION}.tgz -C /opt && \
    rm apache-jmeter-${JMETER_VERSION}.tgz

# Install JMeter plugins manager
RUN wget https://jmeter-plugins.org/get/ -O ${JMETER_HOME}/lib/ext/jmeter-plugins-manager.jar && \
    wget https://repo1.maven.org/maven2/kg/apc/cmdrunner/2.3/cmdrunner-2.3.jar -O ${JMETER_HOME}/lib/cmdrunner-2.3.jar

# Install required plugins directly (especially the VariableThroughputTimer)
RUN mkdir -p ${JMETER_HOME}/lib/ext/lib && \
    wget https://jmeter-plugins.org/downloads/file/JMeterPlugins-Standard-1.4.0.zip -O /tmp/standard-plugins.zip && \
    unzip -o /tmp/standard-plugins.zip -d ${JMETER_HOME} && \
    wget https://jmeter-plugins.org/downloads/file/JMeterPlugins-Extras-1.4.0.zip -O /tmp/extras-plugins.zip && \
    unzip -o /tmp/extras-plugins.zip -d ${JMETER_HOME} && \
    wget https://jmeter-plugins.org/downloads/file/JMeterPlugins-ExtrasLibs-1.4.0.zip -O /tmp/extras-libs.zip && \
    unzip -o /tmp/extras-libs.zip -d ${JMETER_HOME} && \
    rm /tmp/*.zip

# Install required plugins using Command Line tool as backup method
RUN java -cp ${JMETER_HOME}/lib/ext/jmeter-plugins-manager.jar org.jmeterplugins.repository.PluginManagerCMDInstaller && \
    chmod +x ${JMETER_HOME}/bin/PluginsManagerCMD.sh && \
    ${JMETER_HOME}/bin/PluginsManagerCMD.sh install \
    jpgc-casutg \
    jpgc-tst \
    jpgc-dummy \
    jpgc-functions \
    jpgc-cmn-jmeter \
    jpgc-synthesis \
    jpgc-cmd \
    blazemeter-concurrencythreadgroup

# Create directories for test plans, results and logs
RUN mkdir -p /jmeter/scripts /jmeter/results /jmeter/logs

# Copy scripts from the host to the container
COPY scripts/ /jmeter/scripts/
COPY jmeter.properties ${JMETER_HOME}/bin/

# Set working directory
WORKDIR /jmeter

# Entry point
ENTRYPOINT ["jmeter"]