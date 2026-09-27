from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

import streamlit as st

BACKEND_PATH = Path(__file__).parent / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.application.search_service import QueryRejected, SearchOrchestrationService
from app.application.validation_service import QueryValidationService
from app.core.config import get_settings
from app.domain.models import SearchQuery
from app.domain.providers import PROVIDER_REGISTRY, Provider
from app.infrastructure.providers.base import ProviderError
from app.infrastructure.providers.factory import build_gateway


def _build_gateway(provider: Provider, api_key: str, model: str, base_url: str | None):
    return build_gateway(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=get_settings().request_timeout_seconds,
    )


def _history_context(messages: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{message['role']}: {message['content'][:1000]}"
        for message in messages[-6:]
    )


def main() -> None:
    st.set_page_config(page_title="AI Explorer", layout="wide")
    st.title("AI Explorer")
    st.caption("Search focused on Artificial Intelligence topics.")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex

    with st.sidebar:
        st.header("Search settings")
        provider = st.selectbox(
            "Provider",
            options=list(PROVIDER_REGISTRY),
            format_func=lambda item: PROVIDER_REGISTRY[item].label,
        )
        metadata = PROVIDER_REGISTRY[provider]

        if metadata.models:
            model_options = [*metadata.models, "Custom model..."]
            selected_model = st.selectbox(
                "Model",
                options=model_options,
                index=0,
                key=f"model-{provider.value}",
            )
            if selected_model == "Custom model...":
                model = st.text_input("Custom model name", key=f"custom-model-{provider.value}")
            else:
                model = selected_model
        else:
            model = st.text_input("Model", value=metadata.default_model)

        base_url = None
        if metadata.requires_base_url:
            base_url = st.text_input("API base URL", placeholder="https://api.example.com/v1")

        api_key = st.text_input(
            "Provider API key",
            type="password",
            key=f"api-key-{provider.value}",
        )
        st.caption("The key is kept in memory for this session and is not written to disk.")

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.3,
            step=0.1,
        )

        if st.button("Test connection", use_container_width=True):
            if not api_key:
                st.warning("Enter an API key first.")
            elif not model:
                st.warning("Enter a model name first.")
            else:
                try:
                    gateway = _build_gateway(provider, api_key, model, base_url)
                    if asyncio.run(gateway.validate_key()):
                        st.success("Connection verified.")
                    else:
                        st.error("The key or model could not be verified.")
                except ProviderError as error:
                    st.error(str(error))

        if st.button("Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask an AI-related question")
    if not prompt:
        return
    if not api_key:
        st.warning("Add a provider API key in Search settings to search.")
        return
    if not model:
        st.warning("Choose or enter a model in Search settings.")
        return
    if len(prompt) > 2000:
        st.warning("Keep your question to 2,000 characters or fewer.")
        return

    previous_messages = st.session_state.messages.copy()
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            gateway = _build_gateway(provider, api_key, model, base_url)
            service = SearchOrchestrationService(gateway, QueryValidationService(gateway))
            query = SearchQuery(
                text=prompt.strip(),
                session_id=st.session_state.session_id,
                provider=provider,
                model=model,
                temperature=temperature,
            )
            with st.spinner("Validating and searching..."):
                answer = asyncio.run(service.search(query, _history_context(previous_messages)))
            if answer.summary:
                st.info(answer.summary)
            st.markdown(answer.answer_markdown)
            st.caption(f"Model: {answer.model_used}")
            st.session_state.messages.append(
                {"role": "assistant", "content": answer.answer_markdown}
            )
        except QueryRejected as error:
            st.warning(error.message)
            st.session_state.messages.append({"role": "assistant", "content": error.message})
        except ProviderError as error:
            st.error(str(error))
        except Exception:
            st.error("An unexpected error occurred. Please try again.")


if __name__ == "__main__":
    main()