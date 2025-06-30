package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

// AgentfileConfig represents the parsed Agentfile configuration
type AgentfileConfig struct {
	BaseImage              string                  `json:"base_image"`
	Framework              string                  `json:"framework"`
	DefaultModel           string                  `json:"default_model"`
	Secrets                []Secret                `json:"secrets"`
	MCPServers             map[string]MCPServer    `json:"mcp_servers"`
	Agents                 map[string]Agent        `json:"agents"`
	Routers                map[string]Router       `json:"routers"`
	Chains                 map[string]Chain        `json:"chains"`
	Orchestrators          map[string]Orchestrator `json:"orchestrators"`
	ExposePorts            []int                   `json:"expose_ports"`
	CMD                    []string                `json:"cmd"`
	DockerfileInstructions []DockerInstruction     `json:"dockerfile_instructions"`
}

type Secret struct {
	Name  string `json:"name"`
	Value string `json:"value,omitempty"`
}

type MCPServer struct {
	Name      string            `json:"name"`
	Command   string            `json:"command,omitempty"`
	Args      []string          `json:"args,omitempty"`
	Transport string            `json:"transport"`
	URL       string            `json:"url,omitempty"`
	Env       map[string]string `json:"env,omitempty"`
}

type Agent struct {
	Name        string   `json:"name"`
	Instruction string   `json:"instruction"`
	Servers     []string `json:"servers,omitempty"`
	Model       string   `json:"model,omitempty"`
	UseHistory  bool     `json:"use_history"`
	HumanInput  bool     `json:"human_input"`
	Default     bool     `json:"default"`
}

type Router struct {
	Name        string   `json:"name"`
	Agents      []string `json:"agents,omitempty"`
	Model       string   `json:"model,omitempty"`
	Instruction string   `json:"instruction,omitempty"`
	Default     bool     `json:"default"`
}

type Chain struct {
	Name        string   `json:"name"`
	Sequence    []string `json:"sequence,omitempty"`
	Instruction string   `json:"instruction,omitempty"`
	Cumulative  bool     `json:"cumulative"`
	Default     bool     `json:"default"`
}

type DockerInstruction struct {
	Instruction string   `json:"instruction"`
	Args        []string `json:"args"`
}

type Orchestrator struct {
	Name           string `json:"name"`
	PlanType       string `json:"plan_type,omitempty"`
	PlanIterations int    `json:"plan_iterations,omitempty"`
	Default        bool   `json:"default"`
}

type AgentfileParser struct {
	config         *AgentfileConfig
	currentContext string
	currentItem    string
}

func NewAgentfileParser() *AgentfileParser {
	return &AgentfileParser{
		config: &AgentfileConfig{
			BaseImage:              "yeahdongcn/agentman-base:latest",
			Framework:              "fast-agent",
			MCPServers:             make(map[string]MCPServer),
			Agents:                 make(map[string]Agent),
			Routers:                make(map[string]Router),
			Chains:                 make(map[string]Chain),
			Orchestrators:          make(map[string]Orchestrator),
			CMD:                    []string{"python", "agent.py"},
			DockerfileInstructions: []DockerInstruction{},
		},
	}
}

func (p *AgentfileParser) ParseFile(filename string) (*AgentfileConfig, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to open file %s: %w", filename, err)
	}
	defer file.Close()

	return p.ParseReader(file)
}

func (p *AgentfileParser) ParseReader(reader io.Reader) (*AgentfileConfig, error) {
	scanner := bufio.NewScanner(reader)
	var currentLine strings.Builder
	lineNum := 0

	for scanner.Scan() {
		lineNum++
		line := strings.TrimRight(scanner.Text(), " \t")

		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(strings.TrimSpace(line), "#") {
			continue
		}

		// Handle line continuation with backslash
		if strings.HasSuffix(line, "\\") {
			currentLine.WriteString(strings.TrimSuffix(line, "\\"))
			currentLine.WriteString(" ")
			continue
		}

		// Complete line
		currentLine.WriteString(line)
		completeLine := strings.TrimSpace(currentLine.String())
		currentLine.Reset()

		if completeLine != "" {
			if err := p.parseLine(completeLine, lineNum); err != nil {
				return nil, fmt.Errorf("error parsing line %d: %s - %w", lineNum, completeLine, err)
			}
		}
	}

	return p.config, scanner.Err()
}

func (p *AgentfileParser) parseLine(line string, lineNum int) error {
	parts := p.splitRespectingQuotes(line)
	if len(parts) == 0 {
		return nil
	}

	instruction := strings.ToUpper(parts[0])

	switch instruction {
	case "FROM":
		return p.handleFrom(parts)
	case "FRAMEWORK":
		return p.handleFramework(parts)
	case "MODEL":
		if p.currentContext == "agent" || p.currentContext == "router" {
			return p.handleSubInstruction(instruction, parts)
		}
		return p.handleModel(parts)
	case "SECRET":
		return p.handleSecret(parts)
	case "MCP_SERVER", "SERVER":
		return p.handleMCPServer(parts)
	case "AGENT":
		return p.handleAgent(parts)
	case "ROUTER":
		return p.handleRouter(parts)
	case "CHAIN":
		return p.handleChain(parts)
	case "ORCHESTRATOR":
		return p.handleOrchestrator(parts)
	case "API_KEY", "BASE_URL":
		return p.handleSecretKeyValue(parts)
	case "EXPOSE":
		return p.handleExpose(parts)
	case "CMD":
		return p.handleCmd(parts)
	case "ENV":
		// ENV can be either a Dockerfile instruction or sub-instruction
		if p.currentContext == "server" {
			return p.handleSubInstruction(instruction, parts)
		}
		// Handle as regular Dockerfile instruction
		return p.handleDockerfileInstruction(instruction, parts)
	case "COMMAND", "ARGS", "INSTRUCTION", "SERVERS", "AGENTS", "SEQUENCE", "TRANSPORT", "URL", "USE_HISTORY", "HUMAN_INPUT", "DEFAULT", "CUMULATIVE", "PLAN_TYPE", "PLAN_ITERATIONS":
		return p.handleSubInstruction(instruction, parts)
	default:
		// Handle as regular Dockerfile instruction
		return p.handleDockerfileInstruction(instruction, parts)
	}
}

func (p *AgentfileParser) splitRespectingQuotes(line string) []string {
	var parts []string
	var current strings.Builder
	inQuotes := false
	quoteChar := byte(0)

	for i := 0; i < len(line); i++ {
		char := line[i]

		if !inQuotes && (char == '"' || char == '\'') {
			inQuotes = true
			quoteChar = char
			current.WriteByte(char)
		} else if inQuotes && char == quoteChar {
			inQuotes = false
			current.WriteByte(char)
			quoteChar = 0
		} else if !inQuotes && (char == ' ' || char == '\t') {
			if current.Len() > 0 {
				parts = append(parts, current.String())
				current.Reset()
			}
			// Skip whitespace
			for i+1 < len(line) && (line[i+1] == ' ' || line[i+1] == '\t') {
				i++
			}
		} else {
			current.WriteByte(char)
		}
	}

	if current.Len() > 0 {
		parts = append(parts, current.String())
	}

	// Clean quotes from parts
	for i, part := range parts {
		if len(part) >= 2 {
			if (strings.HasPrefix(part, "\"") && strings.HasSuffix(part, "\"")) ||
				(strings.HasPrefix(part, "'") && strings.HasSuffix(part, "'")) {
				parts[i] = part[1 : len(part)-1]
			}
		}
	}

	return parts
}

func (p *AgentfileParser) handleFrom(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("FROM instruction requires at least one argument")
	}
	p.config.BaseImage = parts[1]
	return p.handleDockerfileInstruction("FROM", parts)
}

func (p *AgentfileParser) handleFramework(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("FRAMEWORK instruction requires one argument")
	}
	p.config.Framework = parts[1]
	return nil
}

func (p *AgentfileParser) handleModel(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("MODEL instruction requires one argument")
	}
	p.config.DefaultModel = parts[1]
	return nil
}

func (p *AgentfileParser) handleSecret(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("SECRET instruction requires at least one argument")
	}

	secret := Secret{Name: parts[1]}
	if len(parts) >= 3 {
		secret.Value = parts[2]
	}
	p.config.Secrets = append(p.config.Secrets, secret)
	return nil
}

func (p *AgentfileParser) handleMCPServer(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("MCP_SERVER instruction requires at least one argument")
	}

	server := MCPServer{
		Name:      parts[1],
		Transport: "stdio",
		Env:       make(map[string]string),
	}

	p.config.MCPServers[parts[1]] = server
	p.currentContext = "server"
	p.currentItem = parts[1]
	return nil
}

func (p *AgentfileParser) handleAgent(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("AGENT instruction requires at least one argument")
	}

	agent := Agent{
		Name:       parts[1],
		UseHistory: true,
		HumanInput: false,
		Default:    false,
	}

	p.config.Agents[parts[1]] = agent
	p.currentContext = "agent"
	p.currentItem = parts[1]
	return nil
}

func (p *AgentfileParser) handleRouter(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("ROUTER instruction requires at least one argument")
	}

	router := Router{
		Name:    parts[1],
		Default: false,
	}

	p.config.Routers[parts[1]] = router
	p.currentContext = "router"
	p.currentItem = parts[1]
	return nil
}

func (p *AgentfileParser) handleChain(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("CHAIN instruction requires at least one argument")
	}

	chain := Chain{
		Name:       parts[1],
		Cumulative: false,
		Default:    false,
	}

	p.config.Chains[parts[1]] = chain
	p.currentContext = "chain"
	p.currentItem = parts[1]
	return nil
}

func (p *AgentfileParser) handleOrchestrator(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("ORCHESTRATOR instruction requires at least one argument")
	}

	orchestrator := Orchestrator{
		Name:    parts[1],
		Default: false,
	}

	p.config.Orchestrators[parts[1]] = orchestrator
	p.currentContext = "orchestrator"
	p.currentItem = parts[1]
	return nil
}

func (p *AgentfileParser) handleSecretKeyValue(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("%s instruction requires at least one argument", parts[0])
	}

	// Handle API_KEY and BASE_URL as special secret types
	secretName := parts[0] // API_KEY or BASE_URL
	secretValue := ""
	if len(parts) >= 2 {
		secretValue = parts[1]
	}

	secret := Secret{Name: secretName, Value: secretValue}
	p.config.Secrets = append(p.config.Secrets, secret)
	return nil
}

func (p *AgentfileParser) handleExpose(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("EXPOSE instruction requires at least one argument")
	}

	for _, portStr := range parts[1:] {
		port, err := strconv.Atoi(portStr)
		if err != nil {
			return fmt.Errorf("invalid port number: %s", portStr)
		}
		p.config.ExposePorts = append(p.config.ExposePorts, port)
	}

	return p.handleDockerfileInstruction("EXPOSE", parts)
}

func (p *AgentfileParser) handleCmd(parts []string) error {
	if len(parts) < 2 {
		return fmt.Errorf("CMD instruction requires at least one argument")
	}

	// Parse CMD - handle both array and string formats
	if strings.HasPrefix(parts[1], "[") {
		// Array format like CMD ["python", "agent.py"]
		cmdStr := strings.Join(parts[1:], " ")
		var cmd []string
		if err := json.Unmarshal([]byte(cmdStr), &cmd); err != nil {
			return fmt.Errorf("failed to parse CMD array: %w", err)
		}
		p.config.CMD = cmd
	} else {
		// String format like CMD python agent.py
		p.config.CMD = parts[1:]
	}

	return nil
}

func (p *AgentfileParser) handleSubInstruction(instruction string, parts []string) error {
	if p.currentContext == "" || p.currentItem == "" {
		return fmt.Errorf("%s instruction must be within a context (SERVER, AGENT, ROUTER, CHAIN, ORCHESTRATOR)", instruction)
	}

	switch p.currentContext {
	case "server":
		return p.handleServerSubInstruction(instruction, parts)
	case "agent":
		return p.handleAgentSubInstruction(instruction, parts)
	case "router":
		return p.handleRouterSubInstruction(instruction, parts)
	case "chain":
		return p.handleChainSubInstruction(instruction, parts)
	case "orchestrator":
		return p.handleOrchestratorSubInstruction(instruction, parts)
	default:
		return fmt.Errorf("unknown context: %s", p.currentContext)
	}
}

func (p *AgentfileParser) handleServerSubInstruction(instruction string, parts []string) error {
	server := p.config.MCPServers[p.currentItem]

	switch instruction {
	case "COMMAND":
		if len(parts) < 2 {
			return fmt.Errorf("COMMAND requires one argument")
		}
		server.Command = parts[1]
	case "ARGS":
		if len(parts) < 2 {
			return fmt.Errorf("ARGS requires at least one argument")
		}
		server.Args = parts[1:]
	case "TRANSPORT":
		if len(parts) < 2 {
			return fmt.Errorf("TRANSPORT requires one argument")
		}
		server.Transport = parts[1]
	case "URL":
		if len(parts) < 2 {
			return fmt.Errorf("URL requires one argument")
		}
		server.URL = parts[1]
	case "ENV":
		if len(parts) < 2 {
			return fmt.Errorf("ENV requires at least one argument")
		}

		// Handle both formats: "ENV KEY=VALUE" and "ENV KEY VALUE"
		if len(parts) == 2 {
			// KEY=VALUE format
			envPair := parts[1]
			if strings.Contains(envPair, "=") {
				kv := strings.SplitN(envPair, "=", 2)
				if len(kv) == 2 {
					server.Env[kv[0]] = kv[1]
				} else {
					return fmt.Errorf("invalid ENV format: %s", envPair)
				}
			} else {
				return fmt.Errorf("ENV requires KEY=VALUE format or KEY VALUE format")
			}
		} else if len(parts) >= 3 {
			// KEY VALUE format
			server.Env[parts[1]] = strings.Join(parts[2:], " ")
		}
	}

	p.config.MCPServers[p.currentItem] = server
	return nil
}

func (p *AgentfileParser) handleAgentSubInstruction(instruction string, parts []string) error {
	agent := p.config.Agents[p.currentItem]

	switch instruction {
	case "INSTRUCTION":
		if len(parts) < 2 {
			return fmt.Errorf("INSTRUCTION requires one argument")
		}
		agent.Instruction = strings.Join(parts[1:], " ")
	case "SERVERS":
		if len(parts) < 2 {
			return fmt.Errorf("SERVERS requires at least one argument")
		}
		agent.Servers = parts[1:]
	case "MODEL":
		if len(parts) < 2 {
			return fmt.Errorf("MODEL requires one argument")
		}
		agent.Model = parts[1]
	case "USE_HISTORY":
		if len(parts) < 2 {
			return fmt.Errorf("USE_HISTORY requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("USE_HISTORY must be true or false")
		}
		agent.UseHistory = val
	case "HUMAN_INPUT":
		if len(parts) < 2 {
			return fmt.Errorf("HUMAN_INPUT requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("HUMAN_INPUT must be true or false")
		}
		agent.HumanInput = val
	case "DEFAULT":
		if len(parts) < 2 {
			return fmt.Errorf("DEFAULT requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("DEFAULT must be true or false")
		}
		agent.Default = val
	}

	p.config.Agents[p.currentItem] = agent
	return nil
}

func (p *AgentfileParser) handleRouterSubInstruction(instruction string, parts []string) error {
	router := p.config.Routers[p.currentItem]

	switch instruction {
	case "AGENTS":
		if len(parts) < 2 {
			return fmt.Errorf("AGENTS requires at least one argument")
		}
		router.Agents = parts[1:]
	case "MODEL":
		if len(parts) < 2 {
			return fmt.Errorf("MODEL requires one argument")
		}
		router.Model = parts[1]
	case "INSTRUCTION":
		if len(parts) < 2 {
			return fmt.Errorf("INSTRUCTION requires one argument")
		}
		router.Instruction = strings.Join(parts[1:], " ")
	case "DEFAULT":
		if len(parts) < 2 {
			return fmt.Errorf("DEFAULT requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("DEFAULT must be true or false")
		}
		router.Default = val
	}

	p.config.Routers[p.currentItem] = router
	return nil
}

func (p *AgentfileParser) handleChainSubInstruction(instruction string, parts []string) error {
	chain := p.config.Chains[p.currentItem]

	switch instruction {
	case "SEQUENCE":
		if len(parts) < 2 {
			return fmt.Errorf("SEQUENCE requires at least one argument")
		}
		chain.Sequence = parts[1:]
	case "INSTRUCTION":
		if len(parts) < 2 {
			return fmt.Errorf("INSTRUCTION requires one argument")
		}
		chain.Instruction = strings.Join(parts[1:], " ")
	case "CUMULATIVE":
		if len(parts) < 2 {
			return fmt.Errorf("CUMULATIVE requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("CUMULATIVE must be true or false")
		}
		chain.Cumulative = val
	case "DEFAULT":
		if len(parts) < 2 {
			return fmt.Errorf("DEFAULT requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("DEFAULT must be true or false")
		}
		chain.Default = val
	}

	p.config.Chains[p.currentItem] = chain
	return nil
}

func (p *AgentfileParser) handleOrchestratorSubInstruction(instruction string, parts []string) error {
	orchestrator := p.config.Orchestrators[p.currentItem]

	switch instruction {
	case "PLAN_TYPE":
		if len(parts) < 2 {
			return fmt.Errorf("PLAN_TYPE requires one argument")
		}
		orchestrator.PlanType = parts[1]
	case "PLAN_ITERATIONS":
		if len(parts) < 2 {
			return fmt.Errorf("PLAN_ITERATIONS requires one argument")
		}
		val, err := strconv.Atoi(parts[1])
		if err != nil {
			return fmt.Errorf("PLAN_ITERATIONS must be a number")
		}
		orchestrator.PlanIterations = val
	case "DEFAULT":
		if len(parts) < 2 {
			return fmt.Errorf("DEFAULT requires one argument")
		}
		val, err := strconv.ParseBool(parts[1])
		if err != nil {
			return fmt.Errorf("DEFAULT must be true or false")
		}
		orchestrator.Default = val
	}

	p.config.Orchestrators[p.currentItem] = orchestrator
	return nil
}

func (p *AgentfileParser) handleDockerfileInstruction(instruction string, parts []string) error {
	dockerInstr := DockerInstruction{
		Instruction: instruction,
		Args:        parts[1:],
	}
	p.config.DockerfileInstructions = append(p.config.DockerfileInstructions, dockerInstr)
	return nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <agentfile>\n", os.Args[0])
		os.Exit(1)
	}

	agentfilePath := os.Args[1]

	// Check if the file exists
	if _, err := os.Stat(agentfilePath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Error: Agentfile not found: %s\n", agentfilePath)
		os.Exit(1)
	}

	parser := NewAgentfileParser()
	config, err := parser.ParseFile(agentfilePath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error parsing Agentfile: %v\n", err)
		os.Exit(1)
	}

	// Generate Dockerfile
	dockerfile, err := generateDockerfile(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error generating Dockerfile: %v\n", err)
		os.Exit(1)
	}

	// Write the generated Dockerfile
	fmt.Print(dockerfile)
}

func generateDockerfile(config *AgentfileConfig) (string, error) {
	var dockerfile strings.Builder

	// Add syntax directive for Agentfile frontend
	dockerfile.WriteString("# syntax=agentfile-frontend\n")
	dockerfile.WriteString("# Generated from Agentfile\n\n")

	// Base image
	dockerfile.WriteString(fmt.Sprintf("FROM %s\n\n", config.BaseImage))

	// Add dockerfile instructions first
	for _, instr := range config.DockerfileInstructions {
		if instr.Instruction == "FROM" {
			continue // Already handled
		}
		dockerfile.WriteString(fmt.Sprintf("%s %s\n", instr.Instruction, strings.Join(instr.Args, " ")))
	}

	// Environment variables for secrets (as build args)
	if len(config.Secrets) > 0 {
		dockerfile.WriteString("\n# Secrets as build arguments\n")
		for _, secret := range config.Secrets {
			if secret.Value == "" {
				dockerfile.WriteString(fmt.Sprintf("ARG %s\n", secret.Name))
			} else {
				dockerfile.WriteString(fmt.Sprintf("ARG %s=%s\n", secret.Name, secret.Value))
			}
		}
		dockerfile.WriteString("\n")
	}

	// Generate configuration files
	if len(config.MCPServers) > 0 || len(config.Agents) > 0 || len(config.Routers) > 0 || len(config.Chains) > 0 || len(config.Orchestrators) > 0 {
		dockerfile.WriteString("# Generate agent configuration\n")
		dockerfile.WriteString("RUN mkdir -p /app/config\n")

		// Generate MCP server config
		if len(config.MCPServers) > 0 {
			mcpConfigJSON, err := json.MarshalIndent(config.MCPServers, "", "  ")
			if err != nil {
				return "", fmt.Errorf("failed to marshal MCP config: %w", err)
			}
			dockerfile.WriteString(fmt.Sprintf("RUN echo '%s' > /app/config/mcp_servers.json\n", string(mcpConfigJSON)))
		}

		// Generate agents config
		if len(config.Agents) > 0 {
			agentsConfigJSON, err := json.MarshalIndent(config.Agents, "", "  ")
			if err != nil {
				return "", fmt.Errorf("failed to marshal agents config: %w", err)
			}
			dockerfile.WriteString(fmt.Sprintf("RUN echo '%s' > /app/config/agents.json\n", string(agentsConfigJSON)))
		}

		// Generate routers config
		if len(config.Routers) > 0 {
			routersConfigJSON, err := json.MarshalIndent(config.Routers, "", "  ")
			if err != nil {
				return "", fmt.Errorf("failed to marshal routers config: %w", err)
			}
			dockerfile.WriteString(fmt.Sprintf("RUN echo '%s' > /app/config/routers.json\n", string(routersConfigJSON)))
		}

		// Generate chains config
		if len(config.Chains) > 0 {
			chainsConfigJSON, err := json.MarshalIndent(config.Chains, "", "  ")
			if err != nil {
				return "", fmt.Errorf("failed to marshal chains config: %w", err)
			}
			dockerfile.WriteString(fmt.Sprintf("RUN echo '%s' > /app/config/chains.json\n", string(chainsConfigJSON)))
		}

		// Generate orchestrators config
		if len(config.Orchestrators) > 0 {
			orchestratorsConfigJSON, err := json.MarshalIndent(config.Orchestrators, "", "  ")
			if err != nil {
				return "", fmt.Errorf("failed to marshal orchestrators config: %w", err)
			}
			dockerfile.WriteString(fmt.Sprintf("RUN echo '%s' > /app/config/orchestrators.json\n", string(orchestratorsConfigJSON)))
		}

		dockerfile.WriteString("\n")
	}

	// Generate framework-specific code
	dockerfile.WriteString("# Generate framework-specific code\n")
	if config.Framework == "agno" {
		dockerfile.WriteString("RUN echo 'Generating AGNO agent code...' && \\\n")
		dockerfile.WriteString("    echo 'import agno' > /app/agent.py && \\\n")
		dockerfile.WriteString("    echo 'print(\"AGNO agent started\")' >> /app/agent.py\n")
	} else {
		dockerfile.WriteString("RUN echo 'Generating Fast-Agent code...' && \\\n")
		dockerfile.WriteString("    echo 'import fastagent' > /app/agent.py && \\\n")
		dockerfile.WriteString("    echo 'print(\"Fast-Agent started\")' >> /app/agent.py\n")
	}

	// Expose ports
	if len(config.ExposePorts) > 0 {
		dockerfile.WriteString("\n# Expose ports\n")
		for _, port := range config.ExposePorts {
			dockerfile.WriteString(fmt.Sprintf("EXPOSE %d\n", port))
		}
	}

	// Working directory
	dockerfile.WriteString("\nWORKDIR /app\n")

	// CMD
	if len(config.CMD) > 0 {
		dockerfile.WriteString("\n# Start command\n")
		cmdJSON, err := json.Marshal(config.CMD)
		if err != nil {
			return "", fmt.Errorf("failed to marshal CMD: %w", err)
		}
		dockerfile.WriteString(fmt.Sprintf("CMD %s\n", string(cmdJSON)))
	}

	return dockerfile.String(), nil
}
