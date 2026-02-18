"""Service for handling RPC procedure documentation and explanations."""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class ProcedureExplanation:
    """Model for storing procedure explanation."""
    rpc_name: str
    description: str
    parameters: Dict[str, str]
    returns: str
    example_response: Dict
    use_cases: List[str]
    fields_explained: Dict[str, str]

class ProcedureDocumentationService:
    """Service for documenting and explaining SQL procedures/RPC functions."""
    
    def __init__(self):
        """Initialize the documentation service."""
        self.procedures_db = {}
    
    def register_procedure(
        self,
        rpc_name: str,
        description: str,
        parameters: Dict[str, str],
        returns: str,
        use_cases: List[str],
        fields_explained: Dict[str, str] = None,
        example_response: Dict = None
    ) -> None:
        """
        Register a procedure with full documentation.
        
        Args:
            rpc_name: RPC procedure name (e.g., 'fn_get_assets')
            description: What the procedure does
            parameters: Parameter names and types
            returns: What the procedure returns
            use_cases: Common use cases for this procedure
            fields_explained: Explanation of response fields
            example_response: Example JSON response
        """
        self.procedures_db[rpc_name] = ProcedureExplanation(
            rpc_name=rpc_name,
            description=description,
            parameters=parameters or {},
            returns=returns,
            example_response=example_response or {},
            use_cases=use_cases or [],
            fields_explained=fields_explained or {}
        )
    
    def get_procedure_explanation(self, rpc_name: str) -> Optional[ProcedureExplanation]:
        """Get explanation for a procedure."""
        return self.procedures_db.get(rpc_name)
    
    def explain_response_field(self, rpc_name: str, field_name: str) -> Optional[str]:
        """Get explanation for a specific field in a response."""
        procedure = self.procedures_db.get(rpc_name)
        if procedure and field_name in procedure.fields_explained:
            return procedure.fields_explained[field_name]
        return None
    
    def generate_markdown_docs(self, rpc_name: str = None) -> str:
        """
        Generate Markdown documentation for procedures.
        
        Args:
            rpc_name: Specific RPC to document, or None for all
            
        Returns:
            Markdown formatted documentation
        """
        procedures = {}
        
        if rpc_name:
            proc = self.procedures_db.get(rpc_name)
            if proc:
                procedures[rpc_name] = proc
        else:
            procedures = self.procedures_db
        
        if not procedures:
            return "No procedures documented."
        
        md = "# RPC Procedures Documentation\n\n"
        
        for proc_name, proc in procedures.items():
            md += f"## {proc_name}\n\n"
            md += f"**Description**: {proc.description}\n\n"
            
            # Parameters
            if proc.parameters:
                md += "### Parameters\n\n"
                for param, param_type in proc.parameters.items():
                    md += f"- `{param}` ({param_type})\n"
                md += "\n"
            
            # Returns
            md += f"### Returns\n\n{proc.returns}\n\n"
            
            # Use Cases
            if proc.use_cases:
                md += "### Use Cases\n\n"
                for use_case in proc.use_cases:
                    md += f"- {use_case}\n"
                md += "\n"
            
            # Fields Explained
            if proc.fields_explained:
                md += "### Response Fields\n\n"
                for field, explanation in proc.fields_explained.items():
                    md += f"- **{field}**: {explanation}\n"
                md += "\n"
            
            # Example Response
            if proc.example_response:
                md += "### Example Response\n\n```json\n"
                md += json.dumps(proc.example_response, indent=2)
                md += "\n```\n\n"
        
        return md
    
    def register_asset_procedures(self) -> None:
        """Register documentation for asset-related procedures."""
        
        # fn_get_assets procedure
        self.register_procedure(
            rpc_name="fn_get_assets",
            description="Retrieve a list of assets with pagination and filtering support",
            parameters={
                "page_size": "integer - Number of records per page (default 10)",
                "page_index": "integer - Page number (1-based)",
                "search": "string - Search term for asset name or code",
                "status": "string - Filter by asset status"
            },
            returns="JSON object containing paginated asset records with associated metadata",
            use_cases=[
                "Get list of all assets in the system",
                "Search for specific assets by name or code",
                "Filter assets by condition or location",
                "Implement pagination in UI",
                "Build asset inventory reports"
            ],
            fields_explained={
                "id": "Unique identifier for the asset",
                "code": "Asset code (e.g., 'FEF00970')",
                "name": "Asset name or description (e.g., '4th FLOOR')",
                "vendor": "Vendor/manufacturer information (object with name)",
                "category": "Asset category (object with name, e.g., 'Furniture & Fixtures')",
                "location": "Physical location of asset (object with name, e.g., 'JW Marriott')",
                "condition": "Current condition status (object with name, e.g., 'Fair')",
                "cost_center": "Cost center allocation (object with name, e.g., 'CC-02')",
                "paging.page_size": "Number of records returned per page",
                "paging.page_index": "Current page number",
                "paging.total_records": "Total number of records available",
                "is_success": "Whether the request was successful",
                "status_code": "HTTP status code (200 = success)"
            },
            example_response={
                "data": [
                    {
                        "id": 26,
                        "code": "FEF00970",
                        "name": "4th FLOOR",
                        "vendor": {"name": "Unknown"},
                        "category": {"name": "Furniture & Fixtures"},
                        "location": {"name": "JW Marriott"},
                        "condition": {"name": "Fair"},
                        "cost_center": {"name": "CC-02"}
                    }
                ],
                "paging": {
                    "page_size": 10,
                    "page_index": 1,
                    "total_records": 4553
                },
                "message": "Assets retrieved successfully",
                "is_success": True,
                "status_code": 200
            }
        )
        
        # fn_get_tickets procedure (example)
        self.register_procedure(
            rpc_name="fn_get_tickets",
            description="Retrieve a list of support tickets with filtering and pagination",
            parameters={
                "page_size": "integer - Number of records per page",
                "page_index": "integer - Page number",
                "status": "string - Filter by ticket status (open, closed, pending)"
            },
            returns="JSON object containing paginated ticket records",
            use_cases=[
                "List all support tickets",
                "Filter tickets by status",
                "Implement ticket pagination",
                "Build support statistics reports"
            ],
            fields_explained={
                "id": "Unique ticket identifier",
                "title": "Ticket subject",
                "status": "Current status (open/closed/pending)",
                "priority": "Priority level",
                "created_at": "Creation timestamp",
                "updated_at": "Last update timestamp"
            }
        )

# Global procedure documentation instance
_procedure_docs = ProcedureDocumentationService()
_procedure_docs.register_asset_procedures()

def get_procedure_docs() -> ProcedureDocumentationService:
    """Get the global procedure documentation service."""
    return _procedure_docs
