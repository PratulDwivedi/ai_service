"""
HTTP client for making API requests.
Provides utility functions for GET, POST, PUT, DELETE requests.
"""

import httpx
from typing import Any, Dict, Optional


class HTTPClient:
    """HTTP client wrapper for making API requests."""

    def __init__(self, timeout: float = 30.0):
        """
        Initialize HTTP client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a GET request.
        
        Args:
            url: The URL to request
            headers: Optional headers
            params: Optional query parameters
            
        Returns:
            Response JSON as dictionary
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

    async def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        raise_for_status: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform a POST request.
        
        Args:
            url: The URL to request
            json: JSON body to send
            headers: Optional headers
            params: Optional query parameters
            
        Returns:
            Response JSON as dictionary
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=json,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            if raise_for_status:
                response.raise_for_status()
                return response.json()
            return response

    async def put(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a PUT request.
        
        Args:
            url: The URL to request
            json: JSON body to send
            headers: Optional headers
            params: Optional query parameters
            
        Returns:
            Response JSON as dictionary
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                json=json,
                headers=headers,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform a DELETE request.
        
        Args:
            url: The URL to request
            headers: Optional headers
            params: Optional query parameters
            
        Returns:
            Response JSON as dictionary
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url, headers=headers, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()


# Singleton instance
http_client = HTTPClient()
