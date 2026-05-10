"""
tests/test_retry_handler.py
Tests para retry logic con tenacity.
"""

import pytest
import time
from unittest.mock import patch

from scripts.etl.retry_handler import (
    retry_pipeline,
    is_retryable,
    TransientFailure,
    ValidationFailure,
    get_retry_stats,
    reset_retry_stats,
)


class TestRetryableExceptions:
    """Pruebas de clasificación de excepciones."""

    def test_transient_exceptions_are_retryable(self):
        """Las excepciones transient deben ser retryables."""
        assert is_retryable(ConnectionError("test"))
        assert is_retryable(TimeoutError("test"))
        assert is_retryable(BrokenPipeError("test"))
        assert is_retryable(OSError("test"))

    def test_validation_exceptions_not_retryable(self):
        """Las excepciones de validación no deben ser retryables."""
        assert not is_retryable(ValueError("test"))
        assert not is_retryable(TypeError("test"))
        assert not is_retryable(KeyError("test"))
        assert not is_retryable(FileNotFoundError("test"))
        assert not is_retryable(IndexError("test"))

    def test_custom_transient_failure_is_retryable(self):
        """TransientFailure debe ser retryable."""
        assert is_retryable(TransientFailure("test"))

    def test_custom_validation_failure_not_retryable(self):
        """ValidationFailure no debe ser retryable."""
        assert not is_retryable(ValidationFailure("test"))


class TestRetryDecorator:
    """Pruebas del decorador @retry_pipeline."""

    def test_successful_on_first_attempt(self):
        """Función exitosa en primer intento no debe reintentar."""
        call_count = [0]

        @retry_pipeline(max_attempts=3)
        def successful_func():
            call_count[0] += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count[0] == 1

    def test_retry_on_transient_failure(self):
        """Función debe reintentar en ConnectionError (transient)."""
        call_count = [0]

        @retry_pipeline(max_attempts=3, initial_wait=0.01, max_wait=0.1)
        def flaky_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Network issue")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count[0] == 3

    def test_fail_fast_on_validation_error(self):
        """Función debe fallar rápidamente en ValidationError (no retryable)."""
        call_count = [0]

        @retry_pipeline(max_attempts=3)
        def validation_fail_func():
            call_count[0] += 1
            raise ValueError("Invalid data")

        with pytest.raises(ValueError):
            validation_fail_func()

        assert call_count[0] == 1  # Solo un intento

    def test_max_attempts_exceeded(self):
        """Función debe fallar tras agotar intentos."""
        call_count = [0]

        @retry_pipeline(max_attempts=2, initial_wait=0.01, max_wait=0.1)
        def always_fails():
            call_count[0] += 1
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError):
            always_fails()

        assert call_count[0] == 2  # Exactamente 2 intentos

    def test_exponential_backoff_timing(self):
        """Verificar que hay espera exponencial entre intentos."""
        call_times = []

        @retry_pipeline(max_attempts=3, initial_wait=0.05, max_wait=0.2)
        def slow_func():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ConnectionError("Transient")
            return "success"

        result = slow_func()
        assert result == "success"
        assert len(call_times) == 3

        # Verificar que hay espera entre intentos
        if len(call_times) >= 2:
            wait_1 = call_times[1] - call_times[0]
            # Debería ser >= initial_wait (0.05)
            assert wait_1 >= 0.04  # Tolerancia

    def test_custom_transient_failure_retried(self):
        """TransientFailure personalizado debe ser reintenrado."""
        call_count = [0]

        @retry_pipeline(max_attempts=3, initial_wait=0.01, max_wait=0.1)
        def custom_transient():
            call_count[0] += 1
            if call_count[0] < 2:
                raise TransientFailure("Custom transient error")
            return "success"

        result = custom_transient()
        assert result == "success"
        assert call_count[0] == 2

    def test_custom_validation_failure_not_retried(self):
        """ValidationFailure personalizado no debe ser reintenrado."""
        call_count = [0]

        @retry_pipeline(max_attempts=3)
        def custom_validation_fail():
            call_count[0] += 1
            raise ValidationFailure("Data validation error")

        with pytest.raises(ValidationFailure):
            custom_validation_fail()

        assert call_count[0] == 1  # Solo un intento


class TestRetryStats:
    """Pruebas de estadísticas de reintentos."""

    def test_stats_reset(self):
        """Las estadísticas deben reseteable."""
        reset_retry_stats()
        stats = get_retry_stats()
        assert stats["total_attempts"] == 0

    def test_stats_collection(self):
        """Las estadísticas deben colectarse correctamente."""
        reset_retry_stats()

        @retry_pipeline(max_attempts=2, initial_wait=0.01)
        def some_func():
            return "ok"

        some_func()
        # Nota: stats no se incrementan automáticamente en el decorador básico
        # Este test sirve como placeholder para verificar que la función funciona


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
