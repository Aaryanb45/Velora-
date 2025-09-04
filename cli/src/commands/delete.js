const { Command } = require('commander');
const chalk = require('chalk');
const inquirer = require('inquirer');
const api = require('../utils/api');

const deleteCommand = new Command('delete')
  .description('Delete a service')
  .argument('<service-name-or-id>', 'Service name or ID')
  .option('-f, --force', 'Force delete without confirmation')
  .action(async (serviceIdentifier, options) => {
    try {
      // Find service
      const services = await api.getServices();
      const service = services.find(s => s.name === serviceIdentifier || s.id === serviceIdentifier);
      
      if (!service) {
        console.error(chalk.red(`❌ Service "${serviceIdentifier}" not found`));
        process.exit(1);
      }
      
      // Confirmation
      if (!options.force) {
        console.log(chalk.yellow('⚠️  You are about to delete the following service:'));
        console.log(`  Name: ${service.name}`);
        console.log(`  Type: ${service.service_type}`);
        console.log(`  Status: ${service.status}`);
        if (service.service_url) {
          console.log(`  URL: ${service.service_url}`);
        }
        console.log();
        
        const { confirm } = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'confirm',
            message: 'Are you sure you want to delete this service? This action cannot be undone.',
            default: false
          }
        ]);
        
        if (!confirm) {
          console.log(chalk.blue('Operation cancelled'));
          return;
        }
      }
      
      // Delete service
      console.log(chalk.blue(`🗑️  Deleting service: ${service.name}`));
      
      try {
        await api.deleteService(service.id);
        console.log(chalk.green('✅ Service deleted successfully'));
        
        console.log(chalk.yellow('\n⚠️  Note: This only removes the service from Velora.'));
        console.log(chalk.dim('You may need to manually clean up:'));
        console.log(chalk.dim('  • GitHub repository'));
        console.log(chalk.dim('  • Docker images'));
        console.log(chalk.dim('  • Kubernetes resources'));
        console.log(chalk.dim('  • DNS records'));
        
      } catch (error) {
        console.error(chalk.red(`❌ Failed to delete service: ${error.message}`));
        process.exit(1);
      }
      
    } catch (error) {
      console.error(chalk.red(`❌ Error: ${error.message}`));
      process.exit(1);
    }
  });

module.exports = deleteCommand;