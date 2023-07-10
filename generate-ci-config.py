import yaml
import os

mode = os.environ['mode']
print(mode)

my_yaml = {'image': 'docker/compose:latest',
           'stages': []}

cfg = {'test': {'tags': ['dpdev'], 'environment': 'testing',
                'secret_id': 'google_id_env_ci', 'secret_secret': 'google_secret_env_ci'},
       'dora': {'tags': ['dora'], 'environment': 'production',
                'secret_id': 'google_id_env_dora', 'secret_secret': 'google_secret_env_dora'}}

def build_script(action, in_pipe, in_full):
  dockerprefix = f'docker-compose -f docker-compose.{in_pipe}.yml'
  my_env = cfg[in_pipe]['environment']
  my_machine = cfg[in_pipe]['tags'][0]
  secret_id = cfg[in_pipe]['secret_id']
  secret_secret = cfg[in_pipe]['secret_secret']
  def make_before_statement(in_action, in_service):
    return [f'echo "{in_action.capitalize()}ing the {my_env} {in_service} on {my_machine}..."']
  def make_after_statement(in_action_past, in_service):
    return [f'echo "{my_env.capitalize()} {in_service} successfully {in_action_past} {my_machine}."']
  script = ['docker info'] + ['docker-compose --version']
  match action:
    case "shutdown":
      match in_full:
        case "webapp":
          return [f'{dockerprefix} rm -f -s webapp']
        case "full":
          return [f'{dockerprefix} down']
    case "build":
      match in_full:
        case "webapp":
          build_before_statement = make_before_statement('build', 'webapp')
          build_after_statement = make_after_statement('built on', 'webapp')
          build_statement = [f'{dockerprefix} build webapp']
        case "full":
          build_before_statement = make_before_statement('build', 'webapp and database application')
          build_after_statement = make_after_statement('built on', 'webapp and database application')
          build_statement = ['run -d --name mytmpsource -v baksql:/source -w /source alpine ls']
          build_statement += ['cp mytmpsource:/source/backup.sql /builds/john.krasting/dora/mariadb/']
          build_statement += ['docker stop mytmpsource']
          build_statement += ['docker rm mytmpsource']
          build_statement += [f'{dockerprefix} build']
      script += build_before_statement
      script += ['sed -i \'s/google_id_env_ci/\'${' + secret_id + '}\'/\' .env']
      script += ['sed -i \'s/google_secret_env_ci/\'${' + secret_secret + '}\'/\' .env']
      match in_pipe:
        case "test":
          script += ['sed -i \'/certfile/s/cert\.pem/gfdl.noaa.gov.crt/\' gunicorn/gunicorn-run.sh']
          script += ['sed -i \'/keyfile/s/key\.pem/gfdl.noaa.gov.key/\' gunicorn/gunicorn-run.sh']
      script += build_statement
      script += build_after_statement
      return script
      
    case "deploy":
      script += make_before_statement('deploy', 'webapp and database application')
      script += [f'{dockerprefix} up -d']
      script += make_after_statement('deployed to', 'webapp and database application')
      return script

def build_job_dict(action, in_yaml, in_pipeline, full='webapp'):
  in_yaml['stages'].append(action)
  in_yaml[f'{action}-job'] = {'stage': action, 'script': build_script(action, in_pipeline, full)}
  in_yaml[f'{action}-job'] = in_yaml[f'{action}-job'] | cfg[in_pipeline] 
  del in_yaml[f'{action}-job']['secret_id'] 
  del in_yaml[f'{action}-job']['secret_secret'] 
  return in_yaml
  
match mode.split('-'):
  case ["shutdown", pipeline]:
      my_yaml = build_job_dict('shutdown', my_yaml, pipeline)
  case ["shutdownfull", pipeline]:
      my_yaml = build_job_dict('shutdown', my_yaml, pipeline, full='full')
  case ["build", pipeline]:
      my_yaml = build_job_dict('build', my_yaml, pipeline)
  case ["buildfull", pipeline]:
      my_yaml = build_job_dict('build', my_yaml, pipeline, full='full')
  case ["deploy", pipeline]:
      my_yaml = build_job_dict('deploy', my_yaml, pipeline)
  case ["downandup", pipeline]:
      my_yaml = build_job_dict('shutdown', my_yaml, pipeline)
      my_yaml = build_job_dict('deploy', my_yaml, pipeline)
  case ["standard", pipeline]:
      my_yaml = build_job_dict('shutdown', my_yaml, pipeline)
      my_yaml = build_job_dict('build', my_yaml, pipeline)
      my_yaml = build_job_dict('deploy', my_yaml, pipeline)
  case ["completefull", pipeline]:
      my_yaml = build_job_dict('shutdown', my_yaml, pipeline, full='full')
      my_yaml = build_job_dict('build', my_yaml, pipeline, full='full')
      my_yaml = build_job_dict('deploy', my_yaml, pipeline)
  case _:
    raise KeyError('Unidentified mode provided')

with open('generated-config.yml','w') as fh:
  yaml.dump(my_yaml,fh,default_flow_style=False)

