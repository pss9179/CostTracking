# Anthropic Instrumentation Fix Plan

## Problem
The Anthropic SDK v0.75.0 uses `cached_property` for the `messages` attribute, which means we can't directly access `client_class.messages.create` - we need to access the property value first.

## Current Code (Line 265-272)
```python
if hasattr(client_class, "messages"):
    # Check if already instrumented
    if hasattr(client_class.messages.create, "_llmobserve_instrumented"):  # ❌ FAILS HERE
        ...
    original_create = client_class.messages.create  # ❌ FAILS HERE
```

## Fix Strategy

### Option 1: Access via Instance (Recommended)
Create a temporary instance to access the cached property:

```python
# Create a temporary instance to access cached_property
temp_instance = client_class(api_key="dummy")  # Won't make real calls
messages_obj = temp_instance.messages  # This triggers cached_property
original_create = messages_obj.create  # Now we can access create
```

### Option 2: Use getattr with proper handling
```python
# Get the messages property descriptor
messages_descriptor = getattr(client_class, 'messages', None)
if messages_descriptor:
    # Access via instance
    temp_instance = client_class(api_key="dummy")
    messages_obj = temp_instance.messages
    if hasattr(messages_obj, 'create'):
        original_create = messages_obj.create
```

### Option 3: Patch at Instance Level (Most Robust)
Instead of patching the class, patch when instances are created:

```python
# Store original __init__
original_init = client_class.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    # Now patch messages.create on this instance
    if hasattr(self, 'messages') and hasattr(self.messages, 'create'):
        if not hasattr(self.messages.create, '_llmobserve_instrumented'):
            original_create = self.messages.create
            wrapped = create_safe_wrapper(original_create, "messages.create", ...)
            self.messages.create = wrapped
```

## Recommended Fix (Option 1 - Simplest)

Update `anthropic_instrumentor.py` around line 265:

```python
try:
    # Patch messages.create() - main chat endpoint
    if hasattr(anthropic, "Anthropic"):
        client_class = anthropic.Anthropic
        
        # Handle cached_property: access via instance
        try:
            # Create temporary instance to access cached_property
            temp_instance = client_class(api_key="dummy")
            messages_obj = temp_instance.messages
            
            if hasattr(messages_obj, 'create'):
                # Check if already instrumented
                if hasattr(messages_obj.create, "_llmobserve_instrumented"):
                    logger.debug("[llmobserve] Anthropic already instrumented")
                    return True
                
                # Wrap messages.create()
                original_create = messages_obj.create
                import inspect
                is_async = inspect.iscoroutinefunction(original_create)
                wrapped_create = create_safe_wrapper(original_create, "messages.create", is_async=is_async)
                
                # Patch on the class by replacing the cached_property
                # We need to patch the descriptor itself
                from functools import cached_property as functools_cached_property
                
                # Store original property
                original_messages_prop = client_class.messages
                
                # Create new cached_property that returns patched messages object
                def patched_messages(self):
                    messages = original_messages_prop.__get__(self, client_class)
                    if not hasattr(messages.create, '_llmobserve_instrumented'):
                        messages.create = wrapped_create
                        wrapped_create._llmobserve_instrumented = True
                    return messages
                
                # Replace the cached_property
                client_class.messages = functools_cached_property(patched_messages)
                
                logger.debug("[llmobserve] Instrumented anthropic.Anthropic.messages.create")
        except Exception as e:
            logger.warning(f"[llmobserve] Could not instrument messages.create: {e}")
```

## Simpler Alternative (Patch on Instance Creation)

Actually, the simplest fix is to patch `__init__`:

```python
# Store original __init__
_original_anthropic_init = None

def _patched_anthropic_init(self, *args, **kwargs):
    global _original_anthropic_init
    if _original_anthropic_init:
        _original_anthropic_init(self, *args, **kwargs)
    
    # Patch messages.create on this instance
    if hasattr(self, 'messages'):
        messages_obj = self.messages  # Access cached_property
        if hasattr(messages_obj, 'create') and not hasattr(messages_obj.create, '_llmobserve_instrumented'):
            original_create = messages_obj.create
            import inspect
            is_async = inspect.iscoroutinefunction(original_create)
            wrapped = create_safe_wrapper(original_create, "messages.create", is_async=is_async)
            messages_obj.create = wrapped
            wrapped._llmobserve_instrumented = True

# In instrument_anthropic():
if hasattr(anthropic, "Anthropic"):
    client_class = anthropic.Anthropic
    if not hasattr(client_class.__init__, '_llmobserve_patched'):
        _original_anthropic_init = client_class.__init__
        client_class.__init__ = _patched_anthropic_init
        client_class.__init__._llmobserve_patched = True
```

This patches each instance as it's created, which is more reliable.





