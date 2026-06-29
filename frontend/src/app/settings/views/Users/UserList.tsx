import { ContentSection, MainToolbar } from "@canonical/maas-react-components";
import { SearchBox } from "@canonical/react-components";

import useDebounce from "@/app/base/hooks/useDebouncedValue";
import { useAppLayoutContext } from "@/app/context";
import UsersTable from "@/app/settings/views/Users/components/UsersTable";

const UserList = () => {
  const { setSidebar } = useAppLayoutContext();

  const [searchText, setSearchText] = useState("");
  const debounceSearchText = useDebounce(searchText);

  const handleSearchInput = (inputValue: string) => {
    setSearchText(inputValue);
  };

  return (
    <ContentSection className="user-list">
      <ContentSection.Header>
        <MainToolbar>
          <MainToolbar.Title>Users</MainToolbar.Title>
          <MainToolbar.Controls>
            <SearchBox
              className="user-list__search"
              externallyControlled
              onChange={handleSearchInput}
              placeholder="Search"
            />
            <button
              onClick={() => {
                setSidebar("addUser");
              }}
              type="button"
            >
              Add user
            </button>
          </MainToolbar.Controls>
        </MainToolbar>
      </ContentSection.Header>
      <ContentSection.Content>
        <UsersTable debounceSearchText={debounceSearchText} />
      </ContentSection.Content>
    </ContentSection>
  );
};

export default UserList;
