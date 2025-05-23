import uuid
from datetime import datetime
import os
import random
import time
import re

class KnowledgeBaseAgent:
    """Agent that augments tickets with knowledge base information"""
    
    def __init__(self):
        """Initialize the knowledge base agent"""
        try:
            # Get the absolute path to the data/playbooks directory
            self.knowledge_base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'playbooks')
            print(f"[DEBUG] Knowledge base path: {self.knowledge_base_path}")
            self.knowledge_base = []
            
            # Scan and load actual playbooks from the directory
            self._load_playbooks()
            print(f"[DEBUG] Loaded {len(self.knowledge_base)} knowledge base entries")
        except Exception as e:
            print(f"[ERROR] Error initializing KnowledgeBaseAgent: {e}")
            self.knowledge_base = []
            # Add placeholder data as fallback
            self._add_placeholder_playbooks()
            print(f"[DEBUG] Added {len(self.knowledge_base)} placeholder playbooks")
    
    def _load_playbooks(self):
        """Load playbooks from the knowledge base directory"""
        try:
            if os.path.exists(self.knowledge_base_path):
                for filename in os.listdir(self.knowledge_base_path):
                    if filename.endswith('.md'):
                        playbook_path = os.path.join(self.knowledge_base_path, filename)
                        kb_entry = self._parse_playbook(playbook_path, filename)
                        if kb_entry:
                            self.knowledge_base.append(kb_entry)
            
            # If no playbooks found or error, add placeholder playbooks
            if not self.knowledge_base:
                print("Warning: No playbooks found in directory. Using placeholder data.")
                self._add_placeholder_playbooks()
        except Exception as e:
            print(f"Error loading playbooks: {e}")
            self._add_placeholder_playbooks()
    
    def _parse_playbook(self, playbook_path, filename):
        """Parse a playbook file to extract metadata and content"""
        try:
            with open(playbook_path, 'r') as file:
                content = file.read()
                
                # Extract title from metadata or filename
                title_match = re.search(r'Title:\s*(.+)', content)
                title = title_match.group(1) if title_match else filename.replace('.md', '').replace('-', ' ').title()
                
                # Extract a summary from the overview section
                overview_match = re.search(r'## Overview\s*\n(.*?)\n\s*---', content, re.DOTALL)
                summary = overview_match.group(1).strip() if overview_match else "This playbook provides troubleshooting guidance."
                
                # Extract tags from filename and content
                tags = []
                # Add tags from filename
                for tag in filename.replace('.md', '').split('-'):
                    if tag.strip():
                        tags.append(tag.strip().lower())
                
                # Look for specific keywords in the content for additional tags
                keywords = ['memory', 'cpu', 'disk', 'network', 'database', 'api', 'error', 'timeout']
                for keyword in keywords:
                    if keyword.lower() in content.lower() and keyword.lower() not in tags:
                        tags.append(keyword.lower())
                
                # Format the link to use @data notation
                link = f"@AITinkerers/data/playbooks/{filename}"
                
                return {
                    "id": f"kb-{filename.replace('.md', '')}",
                    "title": title,
                    "content": summary,
                    "full_content": content,
                    "link": link,
                    "tags": tags
                }
        except Exception as e:
            print(f"Error parsing playbook {filename}: {e}")
            return None
    
    def _add_placeholder_playbooks(self):
        """Add placeholder playbook entries when actual files can't be loaded"""
        self.knowledge_base = [
            {
                "id": "kb-001",
                "title": "Database Connection Issues Playbook",
                "content": "Common database connection issues can be resolved by checking connection pools, database health, and network connectivity.",
                "link": "@AITinkerers/data/playbooks/db-connection-playbook.md",
                "tags": ["database", "connection", "timeout"]
            },
            {
                "id": "kb-002",
                "title": "Memory Leak Debugging Guide",
                "content": "Memory leaks can be identified through heap dumps and memory profiling. Check for unclosed resources and large object allocations.",
                "link": "@AITinkerers/data/playbooks/memory-leak-guide.md",
                "tags": ["memory", "leak", "OOM", "out of memory"]
            },
            {
                "id": "kb-003",
                "title": "API Gateway Troubleshooting Steps",
                "content": "API Gateway issues often relate to routing, authentication, or rate limiting. Check logs for 4xx and 5xx errors to pinpoint the source.",
                "link": "@AITinkerers/data/playbooks/api-gateway-troubleshooting.md",
                "tags": ["API", "gateway", "routing", "auth"]
            },
            {
                "id": "kb-004",
                "title": "Microservice Dependency Resolution",
                "content": "When services depend on each other, check health endpoints, circuit breakers, and retry mechanisms to ensure resilient communication.",
                "link": "@AITinkerers/data/playbooks/microservice-dependencies.md",
                "tags": ["microservice", "dependency", "circuit breaker"]
            }
        ]
    
    def search_knowledge_base(self, ticket):
        """
        Search knowledge base for relevant information based on the ticket
        
        Args:
            ticket (dict): The ticket to search knowledge for
            
        Returns:
            list: Relevant knowledge base entries
        """
        print(f"[DEBUG] Searching knowledge base for ticket {ticket.get('id', 'unknown')}")
        
        # Extract search terms from the ticket
        search_terms = []
        
        # Add terms from title and description
        if "title" in ticket:
            search_terms.extend(ticket["title"].lower().split())
        if "description" in ticket:
            search_terms.extend(ticket["description"].lower().split())
        if "issue" in ticket:
            issue = ticket["issue"]
            if "issue_type" in issue:
                search_terms.extend(issue["issue_type"].lower().split())
            if "service" in issue:
                search_terms.extend(issue["service"].lower().split())
        
        print(f"[DEBUG] Extracted search terms: {search_terms}")
        
        # Filter out common words and short terms
        filtered_terms = [term for term in search_terms if len(term) > 3 and term not in ["the", "and", "for", "with", "this", "that"]]
        
        print(f"[DEBUG] Filtered search terms: {filtered_terms}")
        
        # Find relevant knowledge base entries
        relevant_entries = []
        for entry in self.knowledge_base:
            match_score = 0
            
            # Check for tag matches
            for tag in entry.get("tags", []):
                if any(term in tag or tag in term for term in filtered_terms):
                    match_score += 2
            
            # Check for title matches
            title_lower = entry.get("title", "").lower()
            for term in filtered_terms:
                if term in title_lower:
                    match_score += 1
            
            # Check for content matches
            content_lower = entry.get("content", "").lower()
            for term in filtered_terms:
                if term in content_lower:
                    match_score += 0.5
            
            # Add entries with matches
            if match_score > 0:
                entry_copy = entry.copy()
                entry_copy["match_score"] = match_score
                relevant_entries.append(entry_copy)
        
        print(f"[DEBUG] Found {len(relevant_entries)} relevant entries")
        
        # If no relevant entries found, return a random entry
        if not relevant_entries and self.knowledge_base:
            random_entry = random.choice(self.knowledge_base)
            print(f"[DEBUG] No relevant entries found, returning random entry: {random_entry.get('title')}")
            return [random_entry]
        
        # Sort by match score and return top results (max 2)
        relevant_entries.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        result = relevant_entries[:2]
        
        print(f"[DEBUG] Returning top {len(result)} entries: {[entry.get('title') for entry in result]}")
        return result


class TicketService:
    """Service to handle creating tickets for oncall engineers"""
    
    def __init__(self):
        """Initialize the ticket service"""
        # In a real implementation, this might connect to a ticketing system API
        self.tickets = []
        
        # Add virtual AI oncall agent
        self.ai_agent = {
            "id": "ai-oncall-001",
            "name": "AI Oncall Agent",
            "team": "Automated Response"
        }
        
        # Initialize knowledge base agent
        self.knowledge_agent = KnowledgeBaseAgent()
        
        # Regular oncall engineers (kept for reference but not used for assignments)
        self.oncall_engineers = [
            {"id": "eng-001", "name": "Alice Smith", "team": "Backend"},
            {"id": "eng-002", "name": "Bob Johnson", "team": "Infrastructure"},
            {"id": "eng-003", "name": "Charlie Davis", "team": "Frontend"},
            {"id": "eng-004", "name": "Diana Lee", "team": "Database"},
            {"id": "eng-005", "name": "Evan Wilson", "team": "Security"}
        ]
    
    def create_ticket(self, issue):
        """
        Create a ticket for an issue
        
        Args:
            issue (dict): The issue to create a ticket for
            
        Returns:
            dict: The created ticket
        """
        # Always assign to AI oncall agent
        assigned_engineer = self.ai_agent
        
        # Generate ticket ID
        ticket_id = f"TICKET-{str(uuid.uuid4())[:8]}"
        
        # Create ticket
        ticket = {
            "id": ticket_id,
            "title": f"{issue['severity']} {issue['issue_type']} in {issue['service']}",
            "description": issue['description'],
            "status": "Open",
            "created_at": datetime.now().isoformat(),
            "priority": self._map_severity_to_priority(issue['severity']),
            "assigned_to": assigned_engineer,
            "issue": issue,
            "knowledge_base": [],
            "resolution_output": [] 
        }
        
        # Add ticket to list
        self.tickets.append(ticket)
        
        # DO NOT augment with knowledge here. This will be a separate step.
        # ticket = self.augment_ticket_with_knowledge(ticket) 
        
        print(f"[DEBUG] Ticket {ticket_id} created for {issue['service']} - {issue['issue_type']}. Assigned to {assigned_engineer['name']}")
        return ticket

    def augment_ticket_with_kb(self, ticket_to_augment):
        """
        Augment a ticket with knowledge base information.
        This method now expects the actual ticket object.
        """
        if not ticket_to_augment:
            print(f"[ERROR] augment_ticket_with_kb: Called with no ticket.")
            return None

        print(f"[DEBUG] Augmenting ticket {ticket_to_augment['id']} with knowledge base info")
        
        # Find relevant knowledge base entries
        relevant_kb_entries = self.knowledge_agent.search_knowledge_base(ticket_to_augment)
        
        # Update the ticket with knowledge base info
        # Find the ticket in self.tickets and update it
        found_ticket = False
        for i, t in enumerate(self.tickets):
            if t['id'] == ticket_to_augment['id']:
                self.tickets[i]["knowledge_base"] = relevant_kb_entries
                # Return the updated ticket from the list for consistency
                updated_ticket = self.tickets[i] 
                found_ticket = True
                break
        
        if not found_ticket:
            print(f"[ERROR] augment_ticket_with_kb: Ticket {ticket_to_augment['id']} not found in service list.")
            return ticket_to_augment # Return original if not found, though this shouldn't happen

        print(f"[DEBUG] Ticket {updated_ticket['id']} augmented with {len(relevant_kb_entries)} KB entries.")
        return updated_ticket
    
    def _assign_engineer(self, service):
        """
        This method is kept for backward compatibility but is no longer used.
        All tickets are now assigned to the AI oncall agent.
        """
        return self.ai_agent
    
    def _map_severity_to_priority(self, severity):
        """Map severity to priority level"""
        priority_map = {
            "Critical": "P0 - Immediate",
            "High": "P1 - High",
            "Medium": "P2 - Medium",
            "Low": "P3 - Low"
        }
        return priority_map.get(severity, "P2 - Medium")
    
    def get_tickets(self):
        """Get all tickets"""
        return self.tickets
    
    def get_ticket(self, ticket_id):
        """Get a specific ticket by ID"""
        for ticket in self.tickets:
            if ticket['id'] == ticket_id:
                return ticket
        return None

    def append_to_ticket(self, ticket_id, content, field="resolution_output"):
        """Append content to a ticket under a specified field (default: 'resolution_output')."""
        ticket = self.get_ticket(ticket_id)
        if ticket is not None:
            if field not in ticket:
                ticket[field] = []
            ticket[field].append(content)
            return True
        return False

    def mark_ticket_resolved(self, ticket_id):
        """Mark a ticket as resolved by setting its status to 'Resolved'."""
        ticket = self.get_ticket(ticket_id)
        if ticket is not None:
            ticket["status"] = "Resolved"
            return True
        return False 