# docker build -t production_agent_new -f ./src/production_agents/DQN/Dockerfile  --no-cache --progress=plain . &> build_prod_agent_DQN.log & disown
#if a docker image with the same name exists, delete it first
docker rmi production_agent_new || true
# build the docker image for the production agent DQN
docker build -t production_agent_new -f ./src/production_agents/DQN/Dockerfile  .