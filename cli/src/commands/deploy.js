const { Command } = require('commander');
const chalk = require('chalk');
const api = require('../utils/api');

const deployCommand = new Command('deploy')
  .description('Deploy or rollback a service')
  .argument('<service-name-or-id>', 'Service name or ID')
  .option('-f, --follow', 'Follow deployment progress')
  .option('--rollback', 'Rollback to previous version')
  .action(async (serviceIdentifier, options) => {
    try {
      // Find service
      const services = await api.getServices();
      const service = services.find(s => s.name === serviceIdentifier || s.id === serviceIdentifier);
      
      if (!service) {
        console.error(chalk.red(`❌ Service "${serviceIdentifier}" not found`));
        process.exit(1);
      }
      
      if (options.rollback) {
        console.log(chalk.yellow(`🔄 Initiating rollback for: ${service.name}`));
        
        try {
          await api.rollbackService(service.id);
          console.log(chalk.green('✅ Rollback initiated successfully'));
          
          if (options.follow) {
            console.log(chalk.blue('\n👀 Following rollback progress...'));
            await followDeployment(service.id);
          }
        } catch (error) {
          console.error(chalk.red(`❌ Rollback failed: ${error.message}`));
          process.exit(1);
        }
      } else {
        console.log(chalk.blue(`🚀 Triggering deployment for: ${service.name}`));
        console.log(chalk.yellow('Note: Direct deployment triggering not yet implemented'));
        console.log(chalk.dim('Deployments are automatically triggered when code is pushed to GitHub'));
      }
      
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

async function followDeployment(serviceId) {
  const maxAttempts = 60;
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const pipeline = await api.getPipeline(serviceId);
      
      const statusIcon = pipeline.status === 'success' ? '✅' : 
                        pipeline.status === 'failed' ? '❌' : 
                        pipeline.status === 'running' ? '🔄' : '⏳';
      
      console.log(`${statusIcon} ${pipeline.stage.replace('_', ' ')} (${pipeline.progress}%)`);
      
      if (pipeline.status === 'success' || pipeline.status === 'failed') {
        break;
      }
      
      attempts++;
      if (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
      
    } catch (error) {
      console.error(chalk.yellow(`⚠️  Deployment monitoring error: ${error.message}`));
      break;
    }
  }
}

module.exports = deployCommand;