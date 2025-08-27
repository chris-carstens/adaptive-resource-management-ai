## Steps

1. Install Jmeter

```shell
brew install jmeter
```

2. Generate test plan using WorkloadAndConfigGenerator.ipynb 
   - This will create a JMX file 'JM/scripts/jmeterConfigurationFile.jmx'.

3. Run docker container with JMeter

```shell
docker build -t jmeter:latest .

docker run --rm -v ~/jmeter_results:/jmeter/results -v ~/jmeter_logs:/jmeter/logs jmeter:latest -n -t /jmeter/scripts/jmeterConfigurationFile.jmx -l /jmeter/results/results.jtl -j /jmeter/logs/jmeter.log
```

docker run --rm -it curlimages/curl curl http://host.docker.internal:5000/run-fire-detector

4. Generate csv file from JTL results

```shell
cp ~/jmeter_results/results.jtl results.csv
```
