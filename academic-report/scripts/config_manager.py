"""
配置管理器
通用配置与环境变量管理（平台无关，单一路径）

唯一配置来源：academic-report/config/.env（由 .env.example 复制而来）。
配置查找优先级（从高到低）：
  1. 真实环境变量（os.environ，最高优先级，便于 CI/容器临时覆盖）
  2. config/.env 文件（用户配置，唯一持久化来源）
  3. 代码内默认值（各 getter 的 default 参数）

不读取 ~/.hermes/ 或任何其它路径。
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from utils import get_skill_data_dir

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器（平台无关，单一路径）"""

    def __init__(self):
        """初始化配置管理器：定位 config/.env（唯一配置来源）与可选的 config/config.yaml。"""
        data_dir = get_skill_data_dir()
        self.env_path = data_dir / '.env'             # 唯一配置来源
        self.config_path = data_dir / 'config.yaml'   # 可选：非敏感默认值
        self._config_cache = None
        self._load_env_file()

    def _load_env_file(self):
        """
        加载 config/.env 到 os.environ（不覆盖已存在的环境变量）。
        SMTP_* / LLM_* 等密钥写在 .env 里即可被各 getter 读到，无需手动 export；
        真实环境变量优先级仍高于 .env 文件。
        """
        if not self.env_path.exists():
            return
        try:
            for line in self.env_path.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception as e:
            logger.warning("加载 .env 失败: %s", e)

    def load_config(self) -> Dict:
        """
        加载可选的 config.yaml（扁平 schema，顶层即配置键）。

        Returns:
            配置字典（无 config.yaml 则返回空 dict，由各 getter 用默认值兜底）
        """
        if self._config_cache is not None:
            return self._config_cache

        if not self.config_path.exists():
            self._config_cache = {}
            return self._config_cache

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            self._config_cache = config if isinstance(config, dict) else {}
            logger.info(f"已加载配置: {self.config_path}")
            return self._config_cache

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config_cache = {}
            return self._config_cache

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点号分隔的路径）
            default: 默认值

        Returns:
            配置值
        """
        config = self.load_config()

        # 支持点号分隔的路径
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def get_smtp_config(self) -> Dict[str, str]:
        """
        获取 SMTP 配置

        Returns:
            SMTP 配置字典
        """
        return {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'user': os.getenv('SMTP_USER', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
        }

    def validate_smtp_config(self) -> tuple[bool, str]:
        """
        验证 SMTP 配置

        Returns:
            (是否有效, 错误消息)
        """
        config = self.get_smtp_config()

        if not config['user']:
            return False, "未配置 SMTP 用户名（SMTP_USER）"

        if not config['password']:
            return False, "未配置 SMTP 密码（SMTP_PASSWORD）"

        if not config['host']:
            return False, "未配置 SMTP 主机（SMTP_HOST）"

        try:
            port = int(config['port'])
            if port < 1 or port > 65535:
                return False, f"无效的 SMTP 端口: {port}"
        except ValueError:
            return False, f"无效的 SMTP 端口格式: {config['port']}"

        return True, ""

    def get_api_keys(self) -> Dict[str, str]:
        """
        获取 API 密钥

        Returns:
            API 密钥字典
        """
        return {
            'arxiv': os.getenv('ARXIV_API_KEY', ''),
            'semantic_scholar': os.getenv('SEMANTIC_SCHOLAR_API_KEY', ''),
        }

    # --------------------- 环境变量优先取值 helper --------------------- #
    # .env 是唯一配置来源（已被 _load_env_file 注入 os.environ）。
    # 这些 helper 统一「真实环境变量 > config.yaml（可选覆盖）> 默认值」三层回退，
    # 让 .env 中的非敏感参数（语言、结果数等）也能被各 getter 读到。

    def _env_str(self, env_key: str, cfg_key: str, default: str) -> str:
        val = os.getenv(env_key)
        if val and val.strip():
            return val.strip()
        cfg_val = self.get(cfg_key, default)
        return cfg_val if cfg_val else default

    def _env_int(self, env_key: str, cfg_key: str, default: int) -> int:
        val = os.getenv(env_key) or self.get(cfg_key, None)
        if val is None or str(val).strip() == '':
            return default
        try:
            return int(str(val).strip())
        except ValueError:
            return default

    def _env_bool(self, env_key: str, cfg_key: str, default: bool) -> bool:
        val = os.getenv(env_key)
        if val is None or val.strip() == '':
            val = self.get(cfg_key, None)
        if val is None:
            return default
        if isinstance(val, bool):
            return val
        return str(val).strip().lower() in ('1', 'true', 'yes', 'on')

    # ----------------------------- 学术参数 ---------------------------- #

    def get_default_language(self) -> str:
        """获取默认语言设置（DEFAULT_LANGUAGE / default_language）"""
        return self._env_str('DEFAULT_LANGUAGE', 'default_language', 'bilingual')

    def get_default_time_range(self) -> str:
        """获取默认时间范围（DEFAULT_TIME_RANGE / default_time_range）"""
        return self._env_str('DEFAULT_TIME_RANGE', 'default_time_range', '3y')

    def get_max_results(self) -> int:
        """获取最大结果数（MAX_RESULTS / max_results）"""
        return self._env_int('MAX_RESULTS', 'max_results', 50)

    def get_email_recipient(self) -> str:
        """获取默认邮件接收者（EMAIL_RECIPIENT → email_recipient → SMTP_USER）"""
        recipient = self._env_str('EMAIL_RECIPIENT', 'email_recipient', '')
        if not recipient:
            # 回退到 SMTP 用户名（发给自己）
            recipient = self.get_smtp_config().get('user', '')
        return recipient

    def is_include_preprints(self) -> bool:
        """是否包含预印本（INCLUDE_PREPRINTS / include_preprints）"""
        return self._env_bool('INCLUDE_PREPRINTS', 'include_preprints', True)

    def get_min_citation_count(self) -> int:
        """获取最小引用量（MIN_CITATION_COUNT / min_citation_count）"""
        return self._env_int('MIN_CITATION_COUNT', 'min_citation_count', 0)

    def is_filter_highly_cited(self) -> bool:
        """是否启用高被引筛选（FILTER_HIGHLY_CITED / filter_highly_cited）"""
        return self._env_bool('FILTER_HIGHLY_CITED', 'filter_highly_cited', False)

    def get_highly_cited_threshold(self) -> int:
        """获取高被引阈值（HIGHLY_CITED_THRESHOLD / highly_cited_threshold）"""
        return self._env_int('HIGHLY_CITED_THRESHOLD', 'highly_cited_threshold', 100)

    def is_sci_ei_only(self) -> bool:
        """是否仅SCI/EI期刊（SCI_EI_ONLY / sci_ei_only）"""
        return self._env_bool('SCI_EI_ONLY', 'sci_ei_only', False)

    def get_default_query(self) -> str:
        """兜底默认查询主题（DEFAULT_QUERY / default_query）"""
        return self._env_str('DEFAULT_QUERY', 'default_query', '人工智能')

    def get_output_format(self) -> str:
        """报告输出格式（OUTPUT_FORMAT / output_format）"""
        return self._env_str('OUTPUT_FORMAT', 'output_format', 'markdown')

    def get_output_dir(self) -> str:
        """报告输出目录（OUTPUT_DIR / output_dir）"""
        return self._env_str('OUTPUT_DIR', 'output_dir', 'reports')

    def is_send_email(self) -> bool:
        """是否默认发送邮件（SEND_EMAIL / send_email）"""
        return self._env_bool('SEND_EMAIL', 'send_email', True)

    def get_llm_config(self) -> Dict[str, Any]:
        """
        LLM 配置（四要素生成式分析用）。
        优先级：显式 env > config.yaml（llm_* 键，扁平 schema）> 默认。
        默认复用智谱 GLM 的 Anthropic 兼容端点（ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN）。

        enabled: 未显式设置时，有 api_key 即视为启用（无 key 自动回退规则）。
        """
        api_key = (os.getenv("LLM_API_KEY")
                   or os.getenv("ANTHROPIC_AUTH_TOKEN")
                   or os.getenv("ZHIPU_API_KEY")
                   or self.get("llm_api_key", ""))
        base_url = (os.getenv("LLM_BASE_URL")
                    or os.getenv("ANTHROPIC_BASE_URL")
                    or self.get("llm_base_url", "")
                    or "https://open.bigmodel.cn/api/anthropic")
        model = os.getenv("LLM_MODEL") or self.get("llm_model", "") or "glm-5-turbo"
        provider = os.getenv("LLM_PROVIDER") or self.get("llm_provider", "") or "zhipu"

        enabled_env = os.getenv("LLM_ENABLED")
        if enabled_env is not None:
            enabled = enabled_env.strip().lower() in ("1", "true", "yes", "on")
        else:
            enabled_cfg = self.get("llm_enabled", None)
            enabled = bool(api_key) if enabled_cfg is None else bool(enabled_cfg)

        return {
            "enabled": enabled,
            "provider": provider,
            "api_key": api_key or "",
            "base_url": base_url,
            "model": model,
        }

    def reload(self):
        """重新加载配置"""
        self._config_cache = None
        logger.info("配置已重新加载")


# 全局配置管理器实例
_global_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def main():
    """测试配置管理器"""
    import json

    config_manager = ConfigManager()

    print("=== SMTP 配置 ===")
    smtp_config = config_manager.get_smtp_config()
    print(json.dumps(smtp_config, indent=2, ensure_ascii=False))

    print("\n=== 配置验证 ===")
    is_valid, error_msg = config_manager.validate_smtp_config()
    print(f"有效: {is_valid}")
    if error_msg:
        print(f"错误: {error_msg}")

    print("\n=== 学术配置 ===")
    print(f"默认语言: {config_manager.get_default_language()}")
    print(f"默认时间范围: {config_manager.get_default_time_range()}")
    print(f"最大结果数: {config_manager.get_max_results()}")
    print(f"邮件接收者: {config_manager.get_email_recipient()}")
    print(f"包含预印本: {config_manager.is_include_preprints()}")
    print(f"最小引用量: {config_manager.get_min_citation_count()}")
    print(f"高被引筛选: {config_manager.is_filter_highly_cited()}")
    print(f"高被引阈值: {config_manager.get_highly_cited_threshold()}")


if __name__ == '__main__':
    main()
