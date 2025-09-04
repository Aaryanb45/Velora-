const { Command } = require('commander');
const chalk = require('chalk');
const inquirer = require('inquirer');
const ora = require('ora');
const api = require('../utils/api');
const config = require('../utils/config');

const createCommand = new Command('create')
  .description('Create a new service with CI/CD pipeline')
  .argument('<service-name>', 'Service name (lowercase, alphanumeric, hyphens only)')
  .option('-t, --type <type>', 'Service type (api, frontend, worker, database)', 'api')
  .option('-d, --description <desc>', 'Service description')
  .option('--skip-github', 'Skip GitHub repository creation')
  .option('--skip-deploy', 'Skip initial deployment')
  .action(async (serviceName, options) => {
    try {
      console.log(chalk.blue(`🚀 Creating service: ${serviceName}`));
      
      // Validate service name
      if (!/^[a-z0-9-]+$/.test(serviceName)) {
        console.error(chalk.red('❌ Service name must contain only lowercase letters, numbers, and hyphens'));
        process.exit(1);
      }
      
      // Get configuration
      const currentConfig = config.getConfig();
      if (!currentConfig.apiUrl) {
        console.error(chalk.red('❌ API URL not configured. Run "velora config setup" first.'));
        process.exit(1);
      }
      
      // Get description if not provided
      let description = options.description;
      if (!description) {
        const answers = await inquirer.prompt([
          {
            type: 'input',
            name: 'description',
            message: 'Service description:',
            validate: (input) => input.trim().length > 0 || 'Description is required'
          }
        ]);
        description = answers.description;
      }
      
      // Get developer ID (in real app, this would come from auth)
      let developerId = 'default-developer';
      
      const spinner = ora('Creating service...').start();
      
      try {
        // Create service via API
        const serviceData = {
          name: serviceName,
          description: description,
          service_type: options.type,
          developer_id: developerId
        };
        
        const service = await api.createService(serviceData);
        
        spinner.succeed(chalk.green(`✅ Service "${serviceName}" created successfully!`));
        
        console.log(chalk.blue('\n📋 Service Details:'));
        console.log(`  ID: ${service.id}`);
        console.log(`  Name: ${service.name}`);
        console.log(`  Type: ${service.service_type}`);
        console.log(`  Status: ${service.status}`);
        
        // Monitor pipeline if not skipping deployment
        if (!options.skipDeploy) {
          console.log(chalk.blue('\n📊 Monitoring deployment pipeline...'));
          await monitorPipeline(service.id);
        }
        
        console.log(chalk.green('\n🎉 Service creation completed!'));
        console.log(chalk.dim(`\nNext steps:`));
        console.log(chalk.dim(`  • Check status: velora status ${serviceName}`));
        console.log(chalk.dim(`  • View logs: velora logs ${serviceName} --follow`));
        console.log(chalk.dim(`  • List services: velora list`));
        
      } catch (error) {
        spinner.fail(chalk.red('❌ Failed to create service'));
        console.error(chalk.red(`Error: ${error.message}`));
        process.exit(1);
      }
      
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

async function monitorPipeline(serviceId) {
  const maxAttempts = 60; // 5 minutes with 5-second intervals
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const pipeline = await api.getPipeline(serviceId);
      
      const statusIcon = pipeline.status === 'success' ? '✅' : 
                        pipeline.status === 'failed' ? '❌' : 
                        pipeline.status === 'running' ? '🔄' : '⏳';
      
      console.log(`${statusIcon} Pipeline: ${pipeline.stage} (${pipeline.progress}%)`);
      
      if (pipeline.status === 'success') {
        console.log(chalk.green('✅ Deployment completed successfully!'));
        
        // Get service URL
        try {
          const service = await api.getService(serviceId);
          if (service.service_url) {
            console.log(chalk.blue(`🌐 Service URL: ${service.service_url}`));
          }
        } catch (error) {
          // Ignore URL fetch errors
        }
        
        break;
      } else if (pipeline.status === 'failed') {
        console.log(chalk.red('❌ Deployment failed!'));
        if (pipeline.logs && pipeline.logs.length > 0) {
          console.log(chalk.red('Error logs:'));
          pipeline.logs.forEach(log => console.log(chalk.dim(`  ${log}`)));
        }
        break;
      }
      
      attempts++;
      if (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
      
    } catch (error) {
      console.error(chalk.yellow(`⚠️  Pipeline monitoring error: ${error.message}`));
      break;
    }
  }
  
  if (attempts >= maxAttempts) {
    console.log(chalk.yellow('⏰ Pipeline monitoring timed out. Use "velora status" to check progress.'));
  }
}

module.exports = createCommand;