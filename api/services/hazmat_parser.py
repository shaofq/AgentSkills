# -*- coding: utf-8 -*-
"""
SDS文件解析服务 - 使用PyMuPDF提取PDF文本和关键信息
"""
import re
import os
from typing import Optional, Dict, Any, List, Tuple
import fitz  # PyMuPDF

from api.models.hazmat import ExtractedInfo


class SDSParser:
    """SDS文件解析器"""
    
    # GHS象形图关键词映射
    PICTOGRAM_KEYWORDS = {
        'GHS01': ['爆炸', 'explosive', 'bomb'],
        'GHS02': ['火焰', 'flame', '易燃', 'flammable'],
        'GHS03': ['氧化', 'oxidizer', 'flame over circle'],
        'GHS04': ['气瓶', 'gas cylinder', '高压'],
        'GHS05': ['腐蚀', 'corrosion', 'corrosive'],
        'GHS06': ['骷髅', 'skull', 'toxic', '毒性'],
        'GHS07': ['感叹号', 'exclamation', 'irritant'],
        'GHS08': ['健康危害', 'health hazard', '致癌'],
        'GHS09': ['环境', 'environment', '水生'],
    }
    
    # 危险性类别关键词
    HAZARD_CLASS_KEYWORDS = [
        '易燃气体', '易燃液体', '易燃固体', '易燃气溶胶',
        '氧化性气体', '氧化性液体', '氧化性固体',
        '高压气体', '压缩气体', '液化气体', '冷冻液化气体', '溶解气体',
        '急性毒性', '皮肤腐蚀', '严重眼损伤', '皮肤刺激', '眼刺激',
        '呼吸致敏', '皮肤致敏', '生殖细胞致突变性', '致癌性', '生殖毒性',
        '特异性靶器官毒性', '吸入危害',
        '爆炸物', '自反应物质', '有机过氧化物',
        '金属腐蚀物', '自燃液体', '自燃固体', '自热物质',
        '遇水放出易燃气体',
        'Flammable', 'Oxidizing', 'Compressed', 'Toxic', 'Corrosive',
        'Explosive', 'Self-reactive', 'Pyrophoric', 'Self-heating',
        # MSDS格式额外关键词
        'Dangerous Goods', 'Hazardous', 'IMDG', 'DOT', 'IATA',
        'Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
        'Class 6', 'Class 7', 'Class 8', 'Class 9',
        'Packing Group', 'PG I', 'PG II', 'PG III',
        'Marine Pollutant', 'Limited Quantity', 'Excepted Quantity',
    ]
    
    # MSDS章节标题映射（旧格式 -> 新格式章节号）
    MSDS_SECTION_TITLES = {
        2: ['HAZARDS IDENTIFICATION', 'HAZARD IDENTIFICATION', 'COMPOSITION/INFORMATION',
            'HAZARD(S) IDENTIFICATION', 'POTENTIAL HEALTH EFFECTS', 'HEALTH HAZARD DATA'],
        14: ['TRANSPORT INFORMATION', 'TRANSPORTATION INFORMATION', 'SHIPPING INFORMATION',
             'REGULATORY TRANSPORT INFORMATION', 'DOT CLASSIFICATION', 'IMDG CLASSIFICATION'],
    }
    
    def __init__(self):
        self.llm_client = None
        self.use_llm = False
    
    def set_llm_client(self, client, model: str = 'qwen-vl-max-latest'):
        """设置大模型客户端"""
        self.llm_client = client
        self.llm_model = model
        self.use_llm = True
    
    def parse_pdf(self, file_path: str) -> Tuple[ExtractedInfo, str]:
        """
        解析PDF文件，提取关键信息
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            (ExtractedInfo, full_text): 提取的信息和全文
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 使用PyMuPDF提取文本
        full_text = self._extract_text(file_path)
        
        # 提取各部分信息
        extracted = ExtractedInfo()
        
        # 提取产品名称
        extracted.product_name = self._extract_product_name(full_text)
        
        # 提取CAS号
        extracted.cas_number = self._extract_cas_number(full_text)
        
        # 提取第2节（危险性概述）
        section2_text = self._extract_section(full_text, 2)
        extracted.raw_text_section2 = section2_text
        
        # 从第2节提取信息（如果找到）
        search_text = section2_text if section2_text else full_text
        extracted.hazard_class = self._extract_hazard_class(search_text)
        extracted.pictograms = self._extract_pictograms(search_text)
        extracted.signal_word = self._extract_signal_word(search_text)
        extracted.hazard_statements = self._extract_h_statements(search_text)
        extracted.precautionary_statements = self._extract_p_statements(search_text)
        
        # 提取第14节（运输信息）
        section14_text = self._extract_section(full_text, 14)
        extracted.raw_text_section14 = section14_text
        
        # 从第14节提取信息（如果找到），否则全文搜索
        transport_text = section14_text if section14_text else full_text
        extracted.un_number = self._extract_un_number(transport_text)
        extracted.proper_shipping_name = self._extract_shipping_name(transport_text)
        
        # 补充：提取IMDG/DOT运输分类
        extracted.hazard_class = self._merge_transport_class(extracted.hazard_class, full_text)
        
        # 如果仍然没找到UN编号，尝试全文搜索
        if not extracted.un_number:
            extracted.un_number = self._extract_un_number(full_text)
        
        return extracted, full_text
    
    def _extract_text(self, file_path: str) -> str:
        """使用PyMuPDF提取PDF文本"""
        text_parts = []
        
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                text_parts.append(text)
            doc.close()
        except Exception as e:
            print(f"[SDSParser] PDF提取失败: {e}")
            return ""
        
        return "\n".join(text_parts)
    
    def _is_scanned_pdf(self, text: str, file_path: str) -> bool:
        """判断PDF是否为扫描版（图片PDF）"""
        # 如果文本为空或太短，认为是扫描版
        if not text or len(text.strip()) < 100:
            return True
        
        # 计算有效字符比例（字母、数字、中文）
        valid_chars = sum(1 for c in text if c.isalnum() or '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        
        if total_chars == 0:
            return True
        
        ratio = valid_chars / total_chars
        print(f"[SDSParser] 文本有效字符比例: {ratio:.2f}, 总字符: {total_chars}, 有效: {valid_chars}")
        
        # 如果有效字符比例太低，认为是扫描版
        return ratio < 0.3
    
    def _pdf_to_images(self, file_path: str, max_pages: int = 5) -> List[bytes]:
        """将PDF转换为图片（用于OCR）"""
        images = []
        try:
            doc = fitz.open(file_path)
            page_count = min(len(doc), max_pages)
            
            for page_num in range(page_count):
                page = doc[page_num]
                # 使用较高分辨率渲染
                mat = fitz.Matrix(2.0, 2.0)  # 2x缩放
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
                
            doc.close()
            print(f"[SDSParser] PDF转图片完成: {len(images)} 页")
        except Exception as e:
            print(f"[SDSParser] PDF转图片失败: {e}")
        
        return images
    
    def _ocr_with_tesseract(self, file_path: str) -> Optional[str]:
        """使用Tesseract OCR识别扫描版PDF（快速，无需调用API）"""
        try:
            import pytesseract
            from PIL import Image
            import io
        except ImportError:
            print("[SDSParser] pytesseract未安装，跳过传统OCR")
            return None
        
        all_text = []
        try:
            doc = fitz.open(file_path)
            page_count = min(len(doc), 10)  # 最多处理10页
            
            for page_num in range(page_count):
                page = doc[page_num]
                # 使用适中分辨率（150 DPI足够OCR）
                mat = fitz.Matrix(150/72, 150/72)
                pix = page.get_pixmap(matrix=mat)
                
                # 转换为PIL Image
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                # OCR识别（支持中英文）
                try:
                    text = pytesseract.image_to_string(img, lang='eng+chi_sim')
                    if text.strip():
                        all_text.append(text)
                except Exception as e:
                    # 尝试只用英文
                    try:
                        text = pytesseract.image_to_string(img, lang='eng')
                        if text.strip():
                            all_text.append(text)
                    except:
                        pass
                
            doc.close()
            
            result = "\n".join(all_text)
            print(f"[SDSParser] Tesseract OCR完成: {page_count}页, 文本长度={len(result)}")
            return result
            
        except Exception as e:
            print(f"[SDSParser] Tesseract OCR失败: {e}")
            return None
    
    def _extract_section(self, text: str, section_num: int) -> Optional[str]:
        """提取指定章节内容，支持SDS和MSDS格式"""
        # 常见的章节标题模式（SDS格式）
        patterns = [
            # 中文格式
            rf'第\s*{section_num}\s*[部节章].*?(?=第\s*\d+\s*[部节章]|$)',
            rf'{section_num}\s*[\.、]\s*.*?(?=\d+\s*[\.、]|$)',
            # 英文SDS格式
            rf'SECTION\s*{section_num}[:\s\-].*?(?=SECTION\s*\d+|$)',
            rf'{section_num}\s*[\.]\s*[A-Z].*?(?=\d+\s*\.|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0).strip()
        
        # 尝试MSDS格式的章节标题
        if section_num in self.MSDS_SECTION_TITLES:
            for title in self.MSDS_SECTION_TITLES[section_num]:
                # 匹配章节标题到下一个全大写标题
                pattern = rf'{title}[:\s\-].*?(?=[A-Z]{{2,}}[\s\-:]+[A-Z]|$)'
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(0).strip()
        
        return None
    
    def _extract_product_name(self, text: str) -> Optional[str]:
        """提取产品名称"""
        patterns = [
            r'产品名称[：:]\s*(.+?)(?:\n|$)',
            r'Product\s*Name[：:]\s*(.+?)(?:\n|$)',
            r'化学品名称[：:]\s*(.+?)(?:\n|$)',
            r'Chemical\s*Name[：:]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_cas_number(self, text: str) -> Optional[str]:
        """提取CAS号"""
        patterns = [
            r'CAS[号\s#No\.:-]*[：:]\s*(\d{2,7}-\d{2}-\d)',
            r'(\d{2,7}-\d{2}-\d)',  # 通用CAS格式
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_hazard_class(self, text: str) -> List[str]:
        """提取GHS危险性类别"""
        found_classes = []
        text_lower = text.lower()
        
        for keyword in self.HAZARD_CLASS_KEYWORDS:
            if keyword.lower() in text_lower:
                if keyword not in found_classes:
                    found_classes.append(keyword)
        
        # 尝试提取GHS分类编号
        ghs_pattern = r'(?:类别|Category)\s*(\d+[A-Z]?)'
        matches = re.findall(ghs_pattern, text, re.IGNORECASE)
        for m in matches:
            cat = f"类别{m}"
            if cat not in found_classes:
                found_classes.append(cat)
        
        return found_classes if found_classes else None
    
    def _merge_transport_class(self, existing_classes: Optional[List[str]], text: str) -> Optional[List[str]]:
        """提取并合并IMDG/DOT运输分类"""
        found_classes = existing_classes.copy() if existing_classes else []
        
        # IMDG/DOT 分类模式
        transport_patterns = [
            r'(?:IMDG|DOT|IATA|ADR|RID)[:\s]+Class\s*(\d+(?:\.\d+)?)',
            r'Class[:\s]*(\d+(?:\.\d+)?)\s*(?:\(|–|-)',
            r'UN\s*Class[:\s]*(\d+(?:\.\d+)?)',
            r'Hazard\s*Class[:\s]*(\d+(?:\.\d+)?)',
            r'Transport\s*Hazard\s*Class[:\s]*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in transport_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                class_str = f"Class {m}"
                if class_str not in found_classes:
                    found_classes.append(class_str)
        
        # 包装组（Packing Group）
        pg_patterns = [
            r'Packing\s*Group[:\s]*(I{1,3}|[123])',
            r'PG[:\s]*(I{1,3}|[123])',
        ]
        
        for pattern in pg_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pg = match.group(1).upper()
                if pg in ['1', '2', '3']:
                    pg = ['I', 'II', 'III'][int(pg)-1]
                pg_str = f"PG {pg}"
                if pg_str not in found_classes:
                    found_classes.append(pg_str)
        
        # 海洋污染物
        if re.search(r'Marine\s*Pollutant', text, re.IGNORECASE):
            if 'Marine Pollutant' not in found_classes:
                found_classes.append('Marine Pollutant')
        
        return found_classes if found_classes else None
    
    def _extract_pictograms(self, text: str) -> List[str]:
        """提取象形图标识"""
        found_pictograms = []
        text_lower = text.lower()
        
        for ghs_code, keywords in self.PICTOGRAM_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if ghs_code not in found_pictograms:
                        found_pictograms.append(ghs_code)
                    break
        
        # 直接搜索GHS编号
        ghs_matches = re.findall(r'GHS0[1-9]', text, re.IGNORECASE)
        for m in ghs_matches:
            m_upper = m.upper()
            if m_upper not in found_pictograms:
                found_pictograms.append(m_upper)
        
        return found_pictograms if found_pictograms else None
    
    def _extract_signal_word(self, text: str) -> Optional[str]:
        """提取信号词"""
        patterns = [
            r'信号词[：:]\s*(危险|警告)',
            r'Signal\s*Word[：:]\s*(Danger|Warning)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                word = match.group(1).strip()
                return word
        
        # 直接搜索关键词
        if '危险' in text or 'Danger' in text.upper():
            return '危险'
        if '警告' in text or 'Warning' in text.upper():
            return '警告'
        
        return None
    
    def _extract_un_number(self, text: str) -> Optional[str]:
        """提取UN编号"""
        patterns = [
            r'UN[编号\s#No\.:-]*[：:]\s*(UN\s*\d{4})',
            r'(UN\s*\d{4})',
            r'联合国编号[：:]\s*(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                un = match.group(1).strip()
                # 标准化格式
                if not un.upper().startswith('UN'):
                    un = f'UN{un}'
                return un.upper().replace(' ', '')
        
        return None
    
    def _extract_shipping_name(self, text: str) -> Optional[str]:
        """提取运输专用名称"""
        patterns = [
            r'(?:正式运输名称|运输名称|Proper\s*Shipping\s*Name)[：:]\s*(.+?)(?:\n|$)',
            r'(?:Technical\s*Name|品名)[：:]\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 2:  # 过滤太短的匹配
                    return name
        
        return None
    
    def _extract_h_statements(self, text: str) -> List[str]:
        """提取危险性说明(H statements)"""
        # H200-H400系列
        pattern = r'(H\d{3}[A-Za-z]?(?:\s*[+]\s*H\d{3}[A-Za-z]?)*)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        # 去重并排序
        unique = list(set(m.upper() for m in matches))
        return sorted(unique) if unique else None
    
    def _extract_p_statements(self, text: str) -> List[str]:
        """提取防范说明(P statements)"""
        # P100-P500系列
        pattern = r'(P\d{3}[A-Za-z]?(?:\s*[+]\s*P\d{3}[A-Za-z]?)*)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        # 去重并排序
        unique = list(set(m.upper() for m in matches))
        return sorted(unique) if unique else None


class LLMEnhancedParser(SDSParser):
    """大模型增强的SDS解析器"""
    
    def __init__(self, llm_client=None, model: str = 'qwen-vl-max-latest'):
        super().__init__()
        if llm_client:
            self.set_llm_client(llm_client, model)
    
    def parse_with_llm(self, file_path: str) -> Tuple[ExtractedInfo, str]:
        """使用大模型增强解析，支持扫描版PDF的多模态OCR"""
        # 先使用基础解析提取文本
        full_text = self._extract_text(file_path)
        print(f"[SDSParser] 基础文本提取: 文本长度={len(full_text)}")
        
        # 判断是否为扫描版PDF
        is_scanned = self._is_scanned_pdf(full_text, file_path)
        
        if is_scanned:
            # 扫描版PDF：优先使用传统OCR（快速），失败则使用多模态模型
            print(f"[SDSParser] 检测到扫描版PDF，尝试传统OCR...")
            ocr_text = self._ocr_with_tesseract(file_path)
            
            if ocr_text and len(ocr_text.strip()) > 200:
                full_text = ocr_text
                print(f"[SDSParser] 传统OCR成功，文本长度={len(full_text)}")
            elif self.use_llm and self.llm_client:
                # 传统OCR失败，降级到多模态模型
                print(f"[SDSParser] 传统OCR效果不佳，使用多模态OCR...")
                ocr_text = self._ocr_with_vision_model(file_path)
                if ocr_text:
                    full_text = ocr_text
                    print(f"[SDSParser] 多模态OCR完成，文本长度={len(full_text)}")
        
        # 使用提取的文本进行基础解析
        extracted = ExtractedInfo()
        extracted.product_name = self._extract_product_name(full_text)
        extracted.cas_number = self._extract_cas_number(full_text)
        
        section2_text = self._extract_section(full_text, 2)
        extracted.raw_text_section2 = section2_text
        search_text = section2_text if section2_text else full_text
        extracted.hazard_class = self._extract_hazard_class(search_text)
        extracted.pictograms = self._extract_pictograms(search_text)
        extracted.signal_word = self._extract_signal_word(search_text)
        extracted.hazard_statements = self._extract_h_statements(search_text)
        extracted.precautionary_statements = self._extract_p_statements(search_text)
        
        section14_text = self._extract_section(full_text, 14)
        extracted.raw_text_section14 = section14_text
        transport_text = section14_text if section14_text else full_text
        extracted.un_number = self._extract_un_number(transport_text)
        extracted.proper_shipping_name = self._extract_shipping_name(transport_text)
        extracted.hazard_class = self._merge_transport_class(extracted.hazard_class, full_text)
        
        print(f"[SDSParser] 基础解析完成: product_name={extracted.product_name}")
        
        if not self.use_llm or not self.llm_client:
            print(f"[SDSParser] LLM未启用: use_llm={self.use_llm}, llm_client={self.llm_client is not None}")
            return extracted, full_text
        
        # 使用大模型补充和验证
        try:
            print(f"[SDSParser] 调用LLM增强...")
            llm_result = self._llm_extract(full_text, extracted)
            if llm_result:
                print(f"[SDSParser] LLM返回结果: is_hazardous={llm_result.get('is_hazardous')}, hazard_class={llm_result.get('hazard_class')}")
                extracted = self._merge_results(extracted, llm_result)
            else:
                print(f"[SDSParser] LLM返回空结果")
        except Exception as e:
            print(f"[SDSParser] LLM增强失败: {e}")
            import traceback
            traceback.print_exc()
        
        return extracted, full_text
    
    def _ocr_with_vision_model(self, file_path: str) -> Optional[str]:
        """使用多模态视觉模型对扫描版PDF进行OCR（优化版：智能采样+批量处理）"""
        import base64
        
        # 获取PDF总页数
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
        except:
            total_pages = 20
        
        # 智能采样：只识别关键页面
        # SDS/MSDS关键信息通常在：第1-2页（产品信息）、第2节、第14节附近
        key_pages = self._get_key_pages(total_pages)
        print(f"[SDSParser] 智能采样: 总{total_pages}页，选取关键页: {key_pages}")
        
        # 转换关键页面为图片（降低分辨率以提速）
        images = self._pdf_to_images_selective(file_path, key_pages)
        if not images:
            return None
        
        # 批量处理：将多张图片合并为一次请求（最多4张）
        return self._batch_ocr(images, key_pages)
    
    def _get_key_pages(self, total_pages: int) -> List[int]:
        """智能选取关键页面"""
        key_pages = []
        
        # 第1-2页：通常包含产品名称、CAS号
        key_pages.extend([0, 1] if total_pages > 1 else [0])
        
        # 第2节（危险性概述）通常在前几页
        if total_pages > 2:
            key_pages.append(2)
        
        # 第14节（运输信息）通常在后半部分
        if total_pages > 10:
            # 估算第14节位置（通常在60-80%位置）
            section14_page = int(total_pages * 0.7)
            key_pages.extend([section14_page - 1, section14_page, section14_page + 1])
        elif total_pages > 5:
            key_pages.extend([total_pages - 3, total_pages - 2, total_pages - 1])
        
        # 去重并排序，限制最多6页
        key_pages = sorted(set(p for p in key_pages if 0 <= p < total_pages))[:6]
        return key_pages
    
    def _pdf_to_images_selective(self, file_path: str, pages: List[int]) -> List[Tuple[int, bytes]]:
        """选择性转换PDF页面为图片"""
        images = []
        try:
            doc = fitz.open(file_path)
            
            for page_num in pages:
                if page_num >= len(doc):
                    continue
                page = doc[page_num]
                # 使用较低分辨率以提速（1.5x足够OCR）
                mat = fitz.Matrix(1.5, 1.5)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                images.append((page_num, img_bytes))
                
            doc.close()
            print(f"[SDSParser] 选择性转图完成: {len(images)} 页")
        except Exception as e:
            print(f"[SDSParser] PDF转图片失败: {e}")
        
        return images
    
    def _batch_ocr(self, images: List[Tuple[int, bytes]], page_nums: List[int]) -> Optional[str]:
        """批量OCR：一次请求处理多张图片"""
        import base64
        
        if not images:
            return None
        
        # 构建多图请求内容
        content = []
        for page_num, img_bytes in images:
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_base64}"}
            })
        
        # 添加提示词
        content.append({
            "type": "text",
            "text": f"""请识别这{len(images)}张SDS/MSDS安全数据表图片中的所有关键信息。

【重点提取】
1. 产品名称（Product Name）
2. CAS号（CAS Number）
3. 危险性类别（Hazard Classification）：如Class 3 Flammable liquid
4. GHS象形图编号（如GHS02、GHS07）
5. 信号词（Signal Word）：Danger或Warning
6. UN编号（UN Number）：如UN1170
7. 运输分类（Transport Classification）：IMDG Class、Packing Group
8. H声明和P声明

请按页面顺序输出识别内容，格式如：
--- 第X页 ---
[识别内容]

只输出识别到的关键信息，省略无关内容。"""
        })
        
        try:
            response = self.llm_client.chat.completions.create(
                model='qwen-vl-max-latest',
                messages=[{"role": "user", "content": content}],
                temperature=0.1,
                max_tokens=6000
            )
            
            result = response.choices[0].message.content.strip()
            print(f"[SDSParser] 批量OCR完成，文本长度={len(result)}")
            return result
            
        except Exception as e:
            print(f"[SDSParser] 批量OCR失败: {e}")
            # 降级：逐页处理
            return self._fallback_single_ocr(images)
    
    def _fallback_single_ocr(self, images: List[Tuple[int, bytes]]) -> Optional[str]:
        """降级方案：逐页OCR（仅处理前3页）"""
        import base64
        
        all_text = []
        for page_num, img_bytes in images[:3]:  # 最多3页
            try:
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                response = self.llm_client.chat.completions.create(
                    model='qwen-vl-max-latest',
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                            {"type": "text", "text": "识别图片中的所有文字，特别是产品名称、CAS号、危险性类别、UN编号、运输分类。只输出文字内容。"}
                        ]
                    }],
                    temperature=0.1,
                    max_tokens=3000
                )
                
                text = response.choices[0].message.content.strip()
                all_text.append(f"--- 第{page_num+1}页 ---\n{text}")
                print(f"[SDSParser] 降级OCR第{page_num+1}页完成")
                
            except Exception as e:
                print(f"[SDSParser] 降级OCR第{page_num+1}页失败: {e}")
        
        return "\n\n".join(all_text) if all_text else None
    
    def _llm_extract(self, text: str, current: ExtractedInfo) -> Optional[Dict[str, Any]]:
        """使用大模型提取信息"""
        # 截取关键部分，避免token过长
        text_truncated = text[:12000] if len(text) > 12000 else text
        
        prompt = f"""你是一个SDS/MSDS（安全数据表）分析专家，专门识别危险品。请仔细分析以下文档内容，提取所有与危险品判断相关的关键信息。

【重要提示】
- 仔细查找Section 2（危险性概述/Hazards Identification）和Section 14（运输信息/Transport Information）的内容
- 注意识别IMDG/DOT/IATA运输分类（Class 1-9）
- 查找任何危险性相关的关键词：Flammable, Toxic, Corrosive, Oxidizing, Explosive, Irritant等
- 查找包装组(Packing Group)信息：PG I/II/III
- 查找H声明(H statements)和P声明(P statements)
- 如果文档明确标注"Not classified as hazardous"或"Non-dangerous goods"则为非危险品

文档内容:
{text_truncated}

请提取以下信息并以JSON格式返回:
{{
    "product_name": "产品名称（从Section 1或标题提取）",
    "cas_number": "CAS号（格式如：64-17-5）",
    "hazard_class": ["危险性类别列表，包括：GHS分类、IMDG Class、DOT分类等，如：易燃液体、Class 3、Flammable liquid"],
    "pictograms": ["GHS象形图代码列表，如GHS02、GHS07"],
    "signal_word": "信号词（Danger/Warning/危险/警告）",
    "un_number": "UN编号（格式如：UN1170）",
    "proper_shipping_name": "运输专用名称",
    "packing_group": "包装组（I/II/III）",
    "h_statements": ["H声明列表，如H226, H319"],
    "p_statements": ["P声明列表，如P210, P233"],
    "is_hazardous": true或false,
    "hazard_reason": "判断为危险品/非危险品的具体原因，引用文档中的相关内容"
}}

【注意】
- 如果某项信息确实未找到，填null
- is_hazardous判断依据：存在UN编号、危险性分类、GHS象形图、信号词为Danger等任一条件即为true
- 只返回JSON格式，不要任何其他文字说明"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 提取JSON
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            import json
            return json.loads(result_text)
            
        except Exception as e:
            print(f"[SDSParser] LLM调用失败: {e}")
            return None
    
    def _merge_results(self, base: ExtractedInfo, llm_result: Dict[str, Any]) -> ExtractedInfo:
        """合并基础解析和LLM结果"""
        # LLM结果优先：如果LLM提取到信息且基础解析为空，则使用LLM结果
        # 如果都有数据，则合并列表类型的数据
        
        if llm_result.get('product_name') and not base.product_name:
            base.product_name = llm_result['product_name']
        
        if llm_result.get('cas_number') and not base.cas_number:
            base.cas_number = llm_result['cas_number']
        
        # 合并危险性类别
        if llm_result.get('hazard_class'):
            if base.hazard_class:
                # 合并两个列表，去重
                combined = list(set(base.hazard_class + llm_result['hazard_class']))
                base.hazard_class = combined
            else:
                base.hazard_class = llm_result['hazard_class']
        
        # 合并象形图
        if llm_result.get('pictograms'):
            if base.pictograms:
                combined = list(set(base.pictograms + llm_result['pictograms']))
                base.pictograms = combined
            else:
                base.pictograms = llm_result['pictograms']
        
        if llm_result.get('signal_word') and not base.signal_word:
            base.signal_word = llm_result['signal_word']
        
        if llm_result.get('un_number') and not base.un_number:
            base.un_number = llm_result['un_number']
        
        if llm_result.get('proper_shipping_name') and not base.proper_shipping_name:
            base.proper_shipping_name = llm_result['proper_shipping_name']
        
        # 合并H声明
        if llm_result.get('h_statements'):
            if base.hazard_statements:
                combined = list(set(base.hazard_statements + llm_result['h_statements']))
                base.hazard_statements = sorted(combined)
            else:
                base.hazard_statements = llm_result['h_statements']
        
        # 合并P声明
        if llm_result.get('p_statements'):
            if base.precautionary_statements:
                combined = list(set(base.precautionary_statements + llm_result['p_statements']))
                base.precautionary_statements = sorted(combined)
            else:
                base.precautionary_statements = llm_result['p_statements']
        
        # 添加包装组到hazard_class
        if llm_result.get('packing_group'):
            pg = llm_result['packing_group']
            pg_str = f"PG {pg}" if not pg.startswith('PG') else pg
            if base.hazard_class:
                if pg_str not in base.hazard_class:
                    base.hazard_class.append(pg_str)
            else:
                base.hazard_class = [pg_str]
        
        # 保存LLM的判断理由供参考
        if llm_result.get('hazard_reason'):
            # 可以存储在extracted_info中供前端展示
            pass
        
        return base


# 单例
_parser: Optional[LLMEnhancedParser] = None


def get_sds_parser() -> LLMEnhancedParser:
    """获取解析器实例"""
    global _parser
    if _parser is None:
        _parser = LLMEnhancedParser()
    return _parser
