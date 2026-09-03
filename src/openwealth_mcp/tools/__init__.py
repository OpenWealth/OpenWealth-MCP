from openwealth_mcp.custody.app import set_custody_client as set_client
from openwealth_mcp.tools.custody import register_custody_tools
from openwealth_mcp.tools.trading import register_trading_tools, set_trading_client

__all__ = ["register_custody_tools", "register_trading_tools", "set_client", "set_trading_client"]
