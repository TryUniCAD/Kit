#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include <exception>
#include <fcntl.h>
#include <limits>
#include <mach-o/dyld.h>
#include <pthread.h>
#include <stdexcept>
#include <string>
#include <typeinfo>
#include <unordered_set>
#include <unistd.h>
#include <vector>

#if !defined(__APPLE__) || !defined(__arm64__) || !defined(_LIBCPP_VERSION)
#error Unsupported research bridge platform
#endif

#if _LIBCPP_ABI_VERSION != 1 || !defined(_LIBCPP_ABI_ALTERNATE_STRING_LAYOUT)
#error Unsupported libc++ ABI configuration
#endif

namespace Ns {
class MetaType;
class MetaTypeMgr;
class EntityMetaType;
class ValueMetaType;
class MemberMetaType;
class MemberSet;
class Member;
class UniqueString;
}

namespace __cxxabiv1 {
class __class_type_info;
}

namespace {

constexpr std::size_t MaxOutput = 128 * 1024 * 1024;
constexpr std::size_t MaxString = 1024 * 1024;
constexpr std::size_t MaxTypes = 100000;
constexpr std::uint32_t MaxMembers = 65536;
constexpr std::size_t MaxBaseDepth = 128;
constexpr char Deployment[] = "b43a07003c01dd54425db484d23b1c5e6248a21d";

static_assert(sizeof(void*) == 8);
static_assert(sizeof(unsigned int) == 4);
static_assert(sizeof(std::string) == 24);
static_assert(sizeof(std::vector<Ns::MetaType*>) == 24);
static_assert(sizeof(std::type_info) == 16);

class Failure : public std::runtime_error {
public:
    Failure(int value, const std::string& message) : std::runtime_error(message), code(value) {}
    int code;
};

class Json {
public:
    std::string data;

    void raw(const std::string& value) {
        if (value.size() > MaxOutput - data.size()) {
            throw Failure(4, "output limit exceeded");
        }
        data += value;
    }

    void number(std::uint64_t value) {
        raw(std::to_string(value));
    }

    void boolean(bool value) {
        raw(value ? "true" : "false");
    }

    void string(const std::string& value) {
        if (value.size() > MaxString) {
            throw Failure(4, "native string limit exceeded");
        }
        validateUtf8(value);
        raw("\"");
        constexpr char hex[] = "0123456789abcdef";
        for (unsigned char byte : value) {
            if (byte == '"' || byte == '\\') {
                raw(std::string("\\") + static_cast<char>(byte));
            } else if (byte < 0x20) {
                std::string escaped = "\\u00";
                escaped += hex[byte >> 4];
                escaped += hex[byte & 15];
                raw(escaped);
            } else {
                raw(std::string(1, static_cast<char>(byte)));
            }
        }
        raw("\"");
    }

private:
    static void validateUtf8(const std::string& value) {
        std::size_t index = 0;
        while (index < value.size()) {
            auto lead = static_cast<unsigned char>(value[index++]);
            if (lead < 0x80) {
                continue;
            }
            unsigned count = lead >= 0xc2 && lead <= 0xdf ? 1 :
                lead >= 0xe0 && lead <= 0xef ? 2 : lead >= 0xf0 && lead <= 0xf4 ? 3 : 0;
            if (!count || count > value.size() - index) {
                throw Failure(4, "native metadata contains invalid UTF-8");
            }
            std::uint32_t point = lead & ((1u << (6 - count)) - 1);
            for (unsigned position = 0; position < count; ++position) {
                auto next = static_cast<unsigned char>(value[index++]);
                if ((next & 0xc0) != 0x80) {
                    throw Failure(4, "native metadata contains invalid UTF-8");
                }
                point = (point << 6) | (next & 0x3f);
            }
            const std::uint32_t minimum[] = {0, 0x80, 0x800, 0x10000};
            if (point < minimum[count] || point > 0x10ffff ||
                (point >= 0xd800 && point <= 0xdfff)) {
                throw Failure(4, "native metadata contains invalid UTF-8");
            }
        }
    }
};

class Image {
public:
    explicit Image(const char* filename) {
        std::string suffix = std::string("/") + filename;
        for (std::uint32_t index = 0; index < _dyld_image_count(); ++index) {
            const char* found = _dyld_get_image_name(index);
            if (!found) {
                continue;
            }
            std::string candidate(found);
            if (candidate.size() < suffix.size() ||
                candidate.compare(candidate.size() - suffix.size(), suffix.size(), suffix) != 0) {
                continue;
            }
            if (!path.empty()) {
                throw Failure(3, std::string("ambiguous loaded image: ") + filename);
            }
            if (candidate.find(Deployment) == std::string::npos) {
                throw Failure(3, std::string("unexpected deployment: ") + filename);
            }
            path = candidate;
        }
        if (path.empty()) {
            throw Failure(2, std::string("required image is not loaded: ") + filename);
        }
        handle = dlopen(path.c_str(), RTLD_NOW | RTLD_LOCAL | RTLD_NOLOAD);
        if (!handle) {
            const char* error = dlerror();
            throw Failure(2, std::string("cannot retain loaded image: ") + (error ? error : filename));
        }
    }

    ~Image() {
        if (handle) {
            dlclose(handle);
        }
    }

    Image(const Image&) = delete;
    Image& operator=(const Image&) = delete;

    template<class Function>
    Function symbol(const char* name) const {
        dlerror();
        void* address = dlsym(handle, name);
        const char* error = dlerror();
        if (error || !address) {
            throw Failure(2, std::string("missing symbol: ") + name);
        }
        return reinterpret_cast<Function>(address);
    }

    std::string path;

private:
    void* handle = nullptr;
};

using ClassInfo = __cxxabiv1::__class_type_info;
using CastFunction = void* (*)(const void*, const ClassInfo*, const ClassInfo*, std::ptrdiff_t);

const ClassInfo* classInfo(const std::type_info* value) {
    return reinterpret_cast<const ClassInfo*>(value);
}

const std::type_info* checkedBase(const std::type_info* value, const char* name, const char* baseName) {
    if (!value || std::strcmp(value->name(), name) != 0 ||
        std::strcmp(typeid(*value).name(), "N10__cxxabiv120__si_class_type_infoE") != 0) {
        throw Failure(3, std::string("unexpected single-inheritance RTTI: ") + name);
    }
    const std::type_info* base = nullptr;
    const auto* storage = reinterpret_cast<const unsigned char*>(value);
    std::memcpy(&base, storage + sizeof(std::type_info), sizeof(base));
    if (!base || std::strcmp(base->name(), baseName) != 0) {
        throw Failure(3, std::string("unexpected RTTI base: ") + name);
    }
    return base;
}

struct Api {
    Image core{"NsBaseCore10.dylib"};
    Image model{"NsDataModel10.dylib"};
    Ns::MetaTypeMgr* (*registry)() = core.symbol<decltype(registry)>("_ZN2Ns11MetaTypeMgr3getEv");
    void (*types)(const Ns::MetaTypeMgr*, std::vector<Ns::MetaType*>&) =
        core.symbol<decltype(types)>("_ZNK2Ns11MetaTypeMgr9metaTypesERNSt3__16vectorIPNS_8MetaTypeENS1_9allocatorIS4_EEEE");
    const std::string& (*name)(const Ns::MetaType*) = core.symbol<decltype(name)>("_ZNK2Ns8MetaType4nameEv");
    unsigned int (*version)(const Ns::MetaType*) = core.symbol<decltype(version)>("_ZNK2Ns8MetaType7versionEv");
    const Ns::UniqueString* (*identifier)(const Ns::MetaType*) = core.symbol<decltype(identifier)>("_ZNK2Ns8MetaType10identifierEv");
    const Ns::UniqueString* (*baseIdentifier)(const Ns::MetaType*) = core.symbol<decltype(baseIdentifier)>("_ZNK2Ns8MetaType14baseIdentifierEv");
    const std::string& (*addin)(const Ns::MetaType*) = core.symbol<decltype(addin)>("_ZNK2Ns8MetaType15addInIdentifierEv");
    const std::string& (*uniqueName)(const Ns::UniqueString*) = core.symbol<decltype(uniqueName)>("_ZNK2Ns12UniqueString4nameEv");
    const Ns::MemberSet* (*entitySet)(const Ns::EntityMetaType*, unsigned int) =
        model.symbol<decltype(entitySet)>("_ZNK2Ns14EntityMetaType9memberSetEj");
    const Ns::MemberSet* (*valueSet)(const Ns::ValueMetaType*, unsigned int) =
        model.symbol<decltype(valueSet)>("_ZNK2Ns13ValueMetaType9memberSetEj");
    bool (*initialized)(const Ns::MemberSet*) = model.symbol<decltype(initialized)>("_ZNK2Ns9MemberSet11initializedEv");
    unsigned int (*size)(const Ns::MemberSet*) = model.symbol<decltype(size)>("_ZNK2Ns9MemberSet4sizeEv");
    const Ns::Member* (*member)(const Ns::MemberSet*, unsigned int) = model.symbol<decltype(member)>("_ZNK2Ns9MemberSet6memberEj");
    const Ns::MemberSet* (*baseSet)(const Ns::MemberSet*) = model.symbol<decltype(baseSet)>("_ZNK2Ns9MemberSet4baseEv");
    const Ns::MetaType* (*setMeta)(const Ns::MemberSet*) = model.symbol<decltype(setMeta)>("_ZNK2Ns9MemberSet4metaEv");
    const std::string& (*memberId)(const Ns::Member*) = model.symbol<decltype(memberId)>("_ZNK2Ns6Member2idEv");
    const std::string& (*scriptId)(const Ns::Member*) = model.symbol<decltype(scriptId)>("_ZNK2Ns6Member8scriptIdEv");
    const std::string& (*debugType)(const Ns::Member*) = model.symbol<decltype(debugType)>("_ZNK2Ns6Member13debugTypenameEv");
    const Ns::MemberMetaType* (*memberMeta)(const Ns::Member*) = model.symbol<decltype(memberMeta)>("_ZNK2Ns6Member4metaEv");
    unsigned int (*memberCategory)(const Ns::MemberMetaType*) = model.symbol<decltype(memberCategory)>("_ZNK2Ns14MemberMetaType4typeEv");
    bool (*option)(const Ns::Member*, unsigned int) = model.symbol<decltype(option)>("_ZNK2Ns6Member5isSetENS0_13EMemberOptionE");
    const std::type_info* entityRtti = model.symbol<const std::type_info*>("_ZTIN2Ns14EntityMetaTypeE");
    const std::type_info* valueRtti = model.symbol<const std::type_info*>("_ZTIN2Ns13ValueMetaTypeE");
    const std::type_info* metaRtti = nullptr;
    const std::type_info* memberRtti = nullptr;
    CastFunction cast = nullptr;

    Api() {
        metaRtti = checkedBase(entityRtti, "N2Ns14EntityMetaTypeE", "N2Ns8MetaTypeE");
        memberRtti = checkedBase(valueRtti, "N2Ns13ValueMetaTypeE", "N2Ns14MemberMetaTypeE");
        auto otherMeta = checkedBase(memberRtti, "N2Ns14MemberMetaTypeE", "N2Ns8MetaTypeE");
        if (otherMeta != metaRtti) {
            throw Failure(3, "native metatype RTTI base identities differ");
        }
        if (std::strcmp(typeid(*metaRtti).name(), "N10__cxxabiv117__class_type_infoE") != 0) {
            throw Failure(3, "unexpected root metatype RTTI representation");
        }
        dlerror();
        void* address = dlsym(RTLD_DEFAULT, "__dynamic_cast");
        const char* error = dlerror();
        if (error || !address) {
            throw Failure(2, "missing symbol: __dynamic_cast");
        }
        cast = reinterpret_cast<CastFunction>(address);
    }

    void* classify(const Ns::MetaType* value, const std::type_info* target) const {
        if (!value) {
            throw Failure(4, "null registry metatype");
        }
        return cast(value, classInfo(metaRtti), classInfo(target), 0);
    }
};

void writeIdentity(Json& output, const Api& api, const Ns::UniqueString* value) {
    if (value) {
        output.string(api.uniqueName(value));
    } else {
        output.raw("null");
    }
}

void writeCategory(Json& output, const Api& api, const Ns::MemberMetaType* value) {
    unsigned int category = api.memberCategory(value);
    const char* names[] = {"intrinsic", "collection", "pair", "value", "strong_reference", "passive_reference", "optional"};
    if (category >= sizeof(names) / sizeof(names[0])) {
        throw Failure(3, "unknown member metatype category");
    }
    output.raw("{\"value\":");
    output.number(category);
    output.raw(",\"name\":");
    output.string(names[category]);
    output.raw("}");
}

void writeMember(Json& output, const Api& api, const Ns::Member* value, unsigned int index) {
    if (!value) {
        throw Failure(4, "null registered member");
    }
    output.raw("{\"registration_index\":");
    output.number(index);
    output.raw(",\"name\":");
    output.string(api.memberId(value));
    output.raw(",\"script_id\":");
    output.string(api.scriptId(value));
    output.raw(",\"debug_type_name\":");
    output.string(api.debugType(value));
    std::uint32_t mask = 0;
    for (unsigned int bit = 0; bit < 32; ++bit) {
        std::uint32_t flag = std::uint32_t{1} << bit;
        if (api.option(value, flag)) {
            mask |= flag;
        }
    }
    output.raw(",\"option_mask\":");
    output.number(mask);
    auto memberMeta = api.memberMeta(value);
    output.raw(",\"metatype\":");
    if (!memberMeta) {
        output.raw("null");
    } else {
        auto meta = reinterpret_cast<const Ns::MetaType*>(memberMeta);
        if (api.classify(meta, api.memberRtti) != memberMeta) {
            throw Failure(3, "member metatype is not the validated zero-offset base");
        }
        output.raw("{\"name\":");
        output.string(api.name(meta));
        output.raw(",\"identifier\":");
        writeIdentity(output, api, api.identifier(meta));
        output.raw(",\"category\":");
        writeCategory(output, api, memberMeta);
        output.raw("}");
    }
    output.raw("}");
}

void writeSets(Json& output, const Api& api, const Ns::MemberSet* own) {
    if (!own) {
        output.raw("null");
        return;
    }
    std::unordered_set<const Ns::MemberSet*> visited;
    output.raw("[");
    for (auto current = own; current; current = api.baseSet(current)) {
        if (visited.size() >= MaxBaseDepth || !visited.insert(current).second) {
            throw Failure(4, "member-set base cycle or depth limit");
        }
        if (current != own) {
            output.raw(",");
        }
        output.raw("{\"relation\":");
        output.string(current == own ? "own" : "base");
        output.raw(",\"metatype_identifier\":");
        auto meta = api.setMeta(current);
        writeIdentity(output, api, meta ? api.identifier(meta) : nullptr);
        bool ready = api.initialized(current);
        output.raw(",\"initialized\":");
        output.boolean(ready);
        output.raw(",\"members\":");
        if (!ready) {
            output.raw("null");
        } else {
            unsigned int count = api.size(current);
            if (count > MaxMembers) {
                throw Failure(4, "member count exceeds limit");
            }
            output.raw("[");
            for (unsigned int index = 0; index < count; ++index) {
                if (index) {
                    output.raw(",");
                }
                writeMember(output, api, api.member(current, index), index);
            }
            output.raw("]");
        }
        output.raw("}");
    }
    output.raw("]");
}

void writeType(Json& output, const Api& api, const Ns::MetaType* meta) {
    if (!meta) {
        throw Failure(4, "null registered metatype");
    }
    output.raw("{\"name\":");
    output.string(api.name(meta));
    output.raw(",\"identifier\":");
    writeIdentity(output, api, api.identifier(meta));
    output.raw(",\"base_identifier\":");
    writeIdentity(output, api, api.baseIdentifier(meta));
    output.raw(",\"addin\":");
    output.string(api.addin(meta));
    output.raw(",\"version\":");
    output.number(api.version(meta));
    auto entity = static_cast<const Ns::EntityMetaType*>(api.classify(meta, api.entityRtti));
    auto value = static_cast<const Ns::ValueMetaType*>(api.classify(meta, api.valueRtti));
    auto member = static_cast<const Ns::MemberMetaType*>(api.classify(meta, api.memberRtti));
    if (entity && (value || member)) {
        throw Failure(3, "overlapping entity and member RTTI categories");
    }
    output.raw(",\"category\":");
    output.string(entity ? "entity" : value ? "value" : member ? "member" : "other");
    output.raw(",\"member_category\":");
    if (member) {
        writeCategory(output, api, member);
    } else {
        output.raw("null");
    }
    output.raw(",\"member_sets\":");
    constexpr unsigned int currentVersion = std::numeric_limits<unsigned int>::max();
    const Ns::MemberSet* set = entity ? api.entitySet(entity, currentVersion) :
        value ? api.valueSet(value, currentVersion) : nullptr;
    writeSets(output, api, set);
    output.raw("}");
}

std::string capture() {
    if (pthread_main_np() != 1) {
        throw Failure(3, "reflection requires the existing Fusion main-thread task");
    }
    Api api;
    Ns::MetaTypeMgr* manager = api.registry();
    if (!manager) {
        throw Failure(4, "null metatype registry");
    }
    std::vector<Ns::MetaType*> types;
    api.types(manager, types);
    if (types.size() > MaxTypes) {
        throw Failure(4, "registry count exceeds limit");
    }
    Json output;
    output.raw("{\"status\":\"captured_reflection\",\"schema_version\":1,\"expected_fusion_build\":\"2706.1.17\",\"libcxx_header_version\":");
    output.number(_LIBCPP_VERSION);
    output.raw(",\"scope\":\"registered_valid_metatypes_existing_member_sets\",\"wire_schema_complete\":false,\"core_image\":");
    output.string(api.core.path);
    output.raw(",\"model_image\":");
    output.string(api.model.path);
    output.raw(",\"metatype_count\":");
    output.number(types.size());
    output.raw(",\"metatypes\":[");
    for (std::size_t index = 0; index < types.size(); ++index) {
        if (index) {
            output.raw(",");
        }
        writeType(output, api, types[index]);
    }
    output.raw("]}\n");
    return output.data;
}

bool saveNewFile(const char* path, const std::string& data) {
    int descriptor = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    if (descriptor < 0) {
        return false;
    }
    std::size_t position = 0;
    while (position < data.size()) {
        ssize_t count = write(descriptor, data.data() + position, data.size() - position);
        if (count < 0 && errno == EINTR) {
            continue;
        }
        if (count <= 0) {
            close(descriptor);
            return false;
        }
        position += static_cast<std::size_t>(count);
    }
    bool synced = fsync(descriptor) == 0;
    bool closed = close(descriptor) == 0;
    return synced && closed;
}

}

extern "C" __attribute__((visibility("default"))) int dump_schema(const char* path) noexcept {
    if (!path || path[0] != '/' || strnlen(path, 4096) == 4096) {
        return 1;
    }
    int status = 0;
    std::string result;
    try {
        result = capture();
    } catch (const Failure& failure) {
        status = failure.code;
        try {
            Json report;
            report.raw("{\"status\":\"failed\",\"code\":");
            report.number(status);
            report.raw(",\"error\":");
            report.string(failure.what());
            report.raw("}\n");
            result = report.data;
        } catch (...) {
            return 4;
        }
    } catch (const std::exception&) {
        status = 4;
        try {
            result = "{\"status\":\"failed\",\"code\":4,\"error\":\"unexpected C++ exception\"}\n";
        } catch (...) {
            return 4;
        }
    } catch (...) {
        status = 4;
        try {
            result = "{\"status\":\"failed\",\"code\":4,\"error\":\"unknown exception\"}\n";
        } catch (...) {
            return 4;
        }
    }
    return saveNewFile(path, result) ? status : 1;
}
