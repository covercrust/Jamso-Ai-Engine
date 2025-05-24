# Fix to fallback_capital_api.py - May 23, 2025

## Summary of Changes

Fixed type annotation issues in `fallback_capital_api.py` to improve static analysis and prevent type mismatch errors.

## Details

1. Fixed the return type annotation for `convert_to_dataframe` method:
   - Changed from `Optional['pd.DataFrame']` to `Optional[Any]`
   - Added proper imports to handle pandas DataFrame types

2. Added TYPE_CHECKING import for pandas type annotations:
   ```python
   from typing import Dict, List, Any, Optional, Tuple, Union, TYPE_CHECKING
   
   # For type annotations only
   if TYPE_CHECKING:
       import pandas as pd
   ```

## Testing

The fixed code passed static type checking and should work correctly with the pandas DataFrame conversion logic.

## Related Files

- `/home/jamso-ai-server/Jamso-Ai-Engine/src/AI/fallback_capital_api.py`
- `/home/jamso-ai-server/Jamso-Ai-Engine/Docs/type_annotation_fixes_2025-05-23.md`
