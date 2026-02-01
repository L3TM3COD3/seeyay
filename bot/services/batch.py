import asyncio
from typing import List, Callable, Any
from dataclasses import dataclass


@dataclass
class BatchResult:
    """Результат batch-операции"""
    success: bool
    data: Any = None
    error: str = None


class BatchGenerator:
    """
    Класс для batch-генерации с управлением параллельностью
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _run_with_semaphore(
        self, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> BatchResult:
        """Выполняет функцию с ограничением параллельности"""
        async with self.semaphore:
            try:
                result = await func(*args, **kwargs)
                return BatchResult(success=True, data=result)
            except Exception as e:
                return BatchResult(success=False, error=str(e))
    
    async def run_batch(
        self, 
        func: Callable, 
        items: List[Any]
    ) -> List[BatchResult]:
        """
        Выполняет функцию для списка элементов параллельно
        с ограничением max_concurrent одновременных операций
        """
        tasks = [
            self._run_with_semaphore(func, item)
            for item in items
        ]
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def run_batch_with_args(
        self, 
        func: Callable, 
        args_list: List[tuple]
    ) -> List[BatchResult]:
        """
        Выполняет функцию с разными аргументами параллельно
        args_list - список кортежей с аргументами
        """
        tasks = [
            self._run_with_semaphore(func, *args)
            for args in args_list
        ]
        
        results = await asyncio.gather(*tasks)
        return results
