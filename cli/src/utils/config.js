const fs = require('fs-extra');
const path = require('path');
const os = require('os');
const inquirer = require('inquirer');
const chalk = require('chalk');

const CONFIG_DIR = path.join(os.homedir(), '.velora');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

const DEFAULT_CONFIG = {
  apiUrl: 'http://localhost:8001/api',
  githubToken: null,
  dockerRegistry: null,
  dockerToken: null,
  kubeconfig: null
};

function ensureConfigDir() {
  if (!fs.existsSync(CONFIG_DIR)) {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
  }
}

function getConfig() {
  ensureConfigDir();
  
  if (fs.existsSync(CONFIG_FILE)) {
    try {
      const config = fs.readJsonSync(CONFIG_FILE);
      return { ...DEFAULT_CONFIG, ...config };
    } catch (error) {
      console.warn(chalk.yellow('⚠️  Invalid config file, using defaults'));
      return DEFAULT_CONFIG;
    }
  }
  
  return DEFAULT_CONFIG;
}

function setConfig(key, value) {
  ensureConfigDir();
  
  const config = getConfig();
  config[key] = value;
  
  fs.writeJsonSync(CONFIG_FILE, config, { spaces: 2 });
  return config;
}

function resetConfig() {
  ensureConfigDir();
  fs.writeJsonSync(CONFIG_FILE, DEFAULT_CONFIG, { spaces: 2 });
  return DEFAULT_CONFIG;
}

async function setupInteractive() {
  console.log(chalk.blue('🔧 Velora CLI Setup\n'));
  
  const questions = [
    {
      type: 'input',
      name: 'apiUrl',
      message: 'Velora API URL:',
      default: 'http://localhost:8001/api',
      validate: (input) => {
        try {
          new URL(input);
          return true;
        } catch {
          return 'Please enter a valid URL';
        }
      }
    },
    {
      type: 'input',
      name: 'githubToken',
      message: 'GitHub Personal Access Token (optional):',
      default: '',
      transformer: (input) => input ? '●'.repeat(input.length) : '(optional)'
    },
    {
      type: 'input',
      name: 'dockerRegistry',
      message: 'Docker Registry Username (optional):',
      default: ''
    },
    {
      type: 'input',
      name: 'dockerToken',
      message: 'Docker Registry Token (optional):',
      default: '',
      transformer: (input) => input ? '●'.repeat(input.length) : '(optional)'
    }
  ];
  
  const answers = await inquirer.prompt(questions);
  
  // Save configuration
  ensureConfigDir();
  const config = {
    apiUrl: answers.apiUrl,
    githubToken: answers.githubToken || null,
    dockerRegistry: answers.dockerRegistry || null,
    dockerToken: answers.dockerToken || null,
    kubeconfig: null
  };
  
  fs.writeJsonSync(CONFIG_FILE, config, { spaces: 2 });
  
  console.log(chalk.green('\n✅ Configuration saved successfully!'));
  console.log(chalk.dim(`Config file: ${CONFIG_FILE}`));
  
  // Test API connection
  console.log(chalk.blue('\n🔍 Testing API connection...'));
  try {
    const api = require('./api');
    await api.healthCheck();
    console.log(chalk.green('✅ API connection successful!'));
  } catch (error) {
    console.log(chalk.yellow(`⚠️  API connection failed: ${error.message}`));
    console.log(chalk.dim('You can still use the CLI, but some features may not work.'));
  }
  
  return config;
}

function listConfig() {
  const config = getConfig();
  
  console.log(chalk.blue('📋 Current Configuration:\n'));
  
  Object.entries(config).forEach(([key, value]) => {
    const displayValue = value 
      ? (key.toLowerCase().includes('token') || key.toLowerCase().includes('password'))
        ? '●'.repeat(8) + (value.slice(-4) || '')
        : value
      : chalk.dim('(not set)');
    
    console.log(`  ${key.padEnd(15)}: ${displayValue}`);
  });
  
  console.log(chalk.dim(`\nConfig file: ${CONFIG_FILE}`));
}

module.exports = {
  getConfig,
  setConfig,
  resetConfig,
  setupInteractive,
  listConfig,
  CONFIG_FILE,
  CONFIG_DIR
};